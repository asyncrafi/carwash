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
        profile = get_object_or_404(ProviderProfile, user=request.user)
        availability = ProviderAvailability.objects.filter(provider=profile)
        data = ProviderAvailabilitySerializer(availability, many=True).data
        return self.success_response(data=data)

    def post(self, request):
        profile = get_object_or_404(ProviderProfile, user=request.user)
        data = request.data if isinstance(request.data, list) else [request.data]
        results = []
        for item in data:
            serializer = ProviderAvailabilitySerializer(data=item)
            serializer.is_valid(raise_exception=True)
            obj, _ = ProviderAvailability.objects.update_or_create(
                provider=profile,
                day_of_week=serializer.validated_data['day_of_week'],
                defaults={
                    'start_time': serializer.validated_data['start_time'],
                    'end_time': serializer.validated_data['end_time'],
                    'is_active': serializer.validated_data.get('is_active', True),
                },
            )
            results.append(ProviderAvailabilitySerializer(obj).data)
        return self.created_response(
            data=results, message="Availability saved."
        )
