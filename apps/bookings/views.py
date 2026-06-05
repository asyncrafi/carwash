from django.shortcuts import get_object_or_404
from django.db.models import Avg
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny

from apps.core.mixins import BaseResponseMixin
from apps.core.utils import calculate_booking_price
from apps.customers.models import CustomerProfile
from apps.providers.models import ProviderProfile
from apps.ratings.models import Rating
from apps.ratings.serializers import RatingSerializer, TipSerializer
from .models import Booking
from .serializers import (
    BookingCreateSerializer,
    BookingListSerializer,
    BookingDetailSerializer,
    BookingStatusUpdateSerializer,
    JobListSerializer,
)


class BookingCreateView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = get_object_or_404(CustomerProfile, user=request.user)
        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = serializer.validated_data.get('service')
        vehicle = serializer.validated_data.get('vehicle')
        dirt_level = serializer.validated_data.get('dirt_level')
        distance_km = float(serializer.validated_data.get('distance_km', 0.0))

        prices = calculate_booking_price(
            service=service,
            vehicle=vehicle,
            dirt_level=dirt_level,
            distance_km=distance_km,
        )

        booking = serializer.save(
            customer=profile,
            service_price=prices['service_price'],
            vehicle_price=prices['vehicle_price'],
            dirt_price=prices['dirt_price'],
            distance_price=prices['distance_price'],
            engine_discount=prices['engine_discount'],
            platform_fee=prices['platform_fee'],
            total_amount=prices['total_amount'],
        )

        data = BookingDetailSerializer(booking, context={'request': request}).data
        return self.created_response(
            data=data, message="Booking created successfully."
        )


class CustomerBookingListView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = get_object_or_404(CustomerProfile, user=request.user)
        status_f = request.query_params.get('status')
        bookings = Booking.objects.filter(customer=profile).order_by('-created_at')
        if status_f:
            bookings = bookings.filter(status=status_f)
        data = BookingListSerializer(
            bookings, many=True, context={'request': request}
        ).data
        return self.success_response(data=data)


class CustomerBookingDetailView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        profile = get_object_or_404(CustomerProfile, user=request.user)
        booking = get_object_or_404(Booking, pk=pk, customer=profile)
        data = BookingDetailSerializer(booking, context={'request': request}).data
        return self.success_response(data=data)

    def delete(self, request, pk):
        profile = get_object_or_404(CustomerProfile, user=request.user)
        booking = get_object_or_404(Booking, pk=pk, customer=profile)
        if booking.status not in [
            Booking.STATUS_REQUESTED, Booking.STATUS_ACCEPTED
        ]:
            return self.error_response(
                message="Cannot cancel booking at this stage."
            )
        booking.status = Booking.STATUS_CANCELLED
        booking.cancelled_at = timezone.now()
        booking.cancel_reason = request.data.get('cancel_reason', '')
        booking.save()
        return self.success_response(message="Booking cancelled successfully.")


class BookingAddTipView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        profile = get_object_or_404(CustomerProfile, user=request.user)
        booking = get_object_or_404(
            Booking, pk=pk, customer=profile, status=Booking.STATUS_COMPLETED
        )
        if hasattr(booking, 'tip'):
            return self.error_response(message="Tip already added.")
        serializer = TipSerializer(data={
            'booking': booking.id,
            'amount': request.data.get('amount'),
        })
        serializer.is_valid(raise_exception=True)
        serializer.save()
        booking.tip_amount = serializer.validated_data['amount']
        booking.save()
        return self.created_response(
            data=serializer.data, message="Tip added successfully."
        )


class BookingRateView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        profile = get_object_or_404(CustomerProfile, user=request.user)
        booking = get_object_or_404(
            Booking, pk=pk, customer=profile, status=Booking.STATUS_COMPLETED
        )
        if hasattr(booking, 'rating'):
            return self.error_response(message="Already rated.")
        serializer = RatingSerializer(data={
            'booking': booking.id,
            'stars': request.data.get('stars'),
            'comment': request.data.get('comment', ''),
        })
        serializer.is_valid(raise_exception=True)
        rating = serializer.save(
            reviewer=request.user,
            reviewee=booking.provider.user,
        )
        provider = booking.provider
        avg = Rating.objects.filter(reviewee=provider.user).aggregate(
            Avg('stars')
        )['stars__avg']
        provider.average_rating = round(avg or 0, 2)
        provider.save()
        return self.created_response(
            data=RatingSerializer(rating).data, message="Rating submitted."
        )


class ProviderJobListView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = get_object_or_404(ProviderProfile, user=request.user)
        status_f = request.query_params.get('status')
        jobs = Booking.objects.filter(provider=profile).order_by('-created_at')
        if status_f:
            jobs = jobs.filter(status=status_f)
        data = JobListSerializer(
            jobs, many=True, context={'request': request}
        ).data
        return self.success_response(data=data)


class ProviderJobDetailView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        profile = get_object_or_404(ProviderProfile, user=request.user)
        job = get_object_or_404(Booking, pk=pk, provider=profile)
        data = BookingDetailSerializer(job, context={'request': request}).data
        return self.success_response(data=data)


class ProviderJobAcceptView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        profile = get_object_or_404(ProviderProfile, user=request.user)
        booking = get_object_or_404(
            Booking, pk=pk, status=Booking.STATUS_REQUESTED
        )
        booking.provider = profile
        booking.status = Booking.STATUS_ACCEPTED
        booking.accepted_at = timezone.now()
        booking.save()
        return self.success_response(message="Job accepted.")


class ProviderJobRejectView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        return self.success_response(message="Job rejected.")


class ProviderJobStatusUpdateView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        profile = get_object_or_404(ProviderProfile, user=request.user)
        booking = get_object_or_404(Booking, pk=pk, provider=profile)
        serializer = BookingStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data['status']

        valid_transitions = {
            Booking.STATUS_ACCEPTED: [Booking.STATUS_EN_ROUTE],
            Booking.STATUS_EN_ROUTE: [Booking.STATUS_IN_PROGRESS],
            Booking.STATUS_IN_PROGRESS: [Booking.STATUS_COMPLETED],
        }
        allowed = valid_transitions.get(booking.status, [])
        if new_status not in allowed:
            return self.error_response(
                message=(
                    f"Cannot transition from {booking.status} to {new_status}."
                )
            )

        booking.status = new_status
        if new_status == Booking.STATUS_IN_PROGRESS:
            booking.started_at = timezone.now()
        elif new_status == Booking.STATUS_COMPLETED:
            booking.completed_at = timezone.now()
            booking.provider.total_washes += 1
            booking.provider.save()
        booking.save()
        return self.success_response(
            message=f"Status updated to {new_status}."
        )
