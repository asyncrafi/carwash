from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.core.mixins import BaseResponseMixin
from .models import ProviderProfile, ProviderDocument, BankDetail, ProviderAvailability
from .serializers import (
    ProviderProfileSerializer,
    ProviderDocumentSerializer,
    BankDetailSerializer,
    ProviderAvailabilitySerializer,
    ProviderLocationSerializer,
    ProviderOnlineStatusSerializer,
)
from .serializers import ProviderServiceSerializer
from .models import ProviderService
from apps.services.models import Service
from apps.core.utils import haversine_distance_km


class ProviderProfileView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = get_object_or_404(ProviderProfile, user=request.user)
        data = ProviderProfileSerializer(profile).data
        return self.success_response(data=data)

    def patch(self, request):
        profile = get_object_or_404(ProviderProfile, user=request.user)
        serializer = ProviderProfileSerializer(
            profile, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.updated_response(data=serializer.data)


class ProviderOnlineStatusView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        profile = get_object_or_404(ProviderProfile, user=request.user)
        serializer = ProviderOnlineStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile.is_online = serializer.validated_data['is_online']
        profile.save()
        return self.success_response(
            data={'is_online': profile.is_online},
            message="Online status updated.",
        )


class ProviderLocationUpdateView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        profile = get_object_or_404(ProviderProfile, user=request.user)
        serializer = ProviderLocationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile.current_latitude = serializer.validated_data['latitude']
        profile.current_longitude = serializer.validated_data['longitude']
        profile.save()
        return self.success_response(message="Location updated.")


class ProviderDocumentUploadView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = get_object_or_404(ProviderProfile, user=request.user)
        docs = ProviderDocument.objects.filter(provider=profile)
        data = ProviderDocumentSerializer(docs, many=True).data
        return self.success_response(data=data)

    def post(self, request):
        profile = get_object_or_404(ProviderProfile, user=request.user)
        serializer = ProviderDocumentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(provider=profile)
        return self.created_response(
            data=serializer.data, message="Document uploaded successfully."
        )


class ProviderServiceListCreateView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = get_object_or_404(ProviderProfile, user=request.user)
        data = ProviderServiceSerializer(profile.services.all(), many=True).data
        return self.success_response(data=data)

    def post(self, request):
        profile = get_object_or_404(ProviderProfile, user=request.user)
        serializer = ProviderServiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = serializer.validated_data['service']
        obj, created = ProviderService.objects.update_or_create(
            provider=profile, service=service,
            defaults={
                'is_active': serializer.validated_data.get('is_active', True),
                'price_override': serializer.validated_data.get('price_override')
            }
        )
        return self.created_response(data=ProviderServiceSerializer(obj).data)


class ProviderServiceDeleteView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        profile = get_object_or_404(ProviderProfile, user=request.user)
        obj = get_object_or_404(ProviderService, pk=pk, provider=profile)
        obj.delete()
        return self.deleted_response(message="Service removed.")


class ProviderServiceAreaView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        profile = get_object_or_404(ProviderProfile, user=request.user)
        # accept fields: service_address, service_latitude, service_longitude, service_radius_km
        for f in ['service_address', 'service_latitude', 'service_longitude', 'service_radius_km']:
            if f in request.data:
                setattr(profile, f, request.data.get(f))
        profile.save()
        return self.updated_response(data=ProviderProfileSerializer(profile).data, message="Service area updated.")


class ProviderSubmitForReviewView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = get_object_or_404(ProviderProfile, user=request.user)
        # Mark provider as pending review
        profile.status = ProviderProfile.STATUS_PENDING
        profile.save()
        return self.success_response(message="Profile submitted for review.")


class BankDetailView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = get_object_or_404(ProviderProfile, user=request.user)
        bank = get_object_or_404(BankDetail, provider=profile)
        data = BankDetailSerializer(bank).data
        return self.success_response(data=data)

    def post(self, request):
        profile = get_object_or_404(ProviderProfile, user=request.user)
        serializer = BankDetailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        BankDetail.objects.update_or_create(
            provider=profile, defaults=serializer.validated_data
        )
        return self.created_response(
            data=serializer.data, message="Bank details saved."
        )


class ProviderAvailabilityView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get provider availability for all days of the week"""
        profile = get_object_or_404(ProviderProfile, user=request.user)
        availability = ProviderAvailability.objects.filter(provider=profile)
        
        # Create a full week schedule (0-6 for Monday-Sunday)
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        week_schedule = []
        available_days = []
        start_time = None
        end_time = None
        
        for day_num in range(7):
            day_availability = availability.filter(day_of_week=day_num).first()
            if day_availability:
                available_days.append(day_names[day_num])
                if start_time is None:
                    start_time = str(day_availability.start_time)
                    end_time = str(day_availability.end_time)
                day_data = ProviderAvailabilitySerializer(day_availability).data
            else:
                day_data = {
                    'id': None,
                    'day_of_week': day_num,
                    'day_display': day_names[day_num],
                    'start_time': None,
                    'end_time': None,
                    'is_active': False,
                }
            week_schedule.append(day_data)
        
        return self.success_response(
            data={
                'week_schedule': week_schedule,
                'available_days': available_days,
                'available_days_count': len(available_days),
                'start_time': start_time,
                'end_time': end_time,
            }
        )

    def post(self, request):
        """
        Save provider availability for multiple weekdays with one time slot.
        Request format:
        {
            "days": [0, 1, 2, 3, 4],  # Monday-Friday (0-6)
            "start_time": "08:00",
            "end_time": "18:00",
            "is_active": true
        }
        """
        profile = get_object_or_404(ProviderProfile, user=request.user)
        
        days = request.data.get('days', [])
        start_time = request.data.get('start_time')
        end_time = request.data.get('end_time')
        is_active = request.data.get('is_active', True)
        
        if not days or not start_time or not end_time:
            return self.error_response(
                message="Missing required fields: days (list), start_time, end_time"
            )
        
        results = []
        available_days = []
        
        # Create/update availability for each selected day
        for day_of_week in days:
            obj, _ = ProviderAvailability.objects.update_or_create(
                provider=profile,
                day_of_week=day_of_week,
                defaults={
                    'start_time': start_time,
                    'end_time': end_time,
                    'is_active': is_active,
                },
            )
            if obj.is_active:
                available_days.append(obj.get_day_of_week_display())
            results.append(ProviderAvailabilitySerializer(obj).data)
        
        return self.created_response(
            data={
                'availability': results,
                'available_days': available_days,
                'total_available_days': len(available_days),
                'start_time': str(start_time),
                'end_time': str(end_time),
            },
            message="Availability saved."
        )
