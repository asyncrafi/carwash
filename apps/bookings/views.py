from django.shortcuts import get_object_or_404
from django.db.models import Avg
from django.utils import timezone
from datetime import timedelta

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny

from apps.core.mixins import BaseResponseMixin
from apps.core.utils import calculate_booking_price, haversine_distance_km
from apps.customers.models import CustomerProfile
from apps.providers.models import ProviderProfile
from apps.ratings.models import Rating
from apps.ratings.serializers import RatingSerializer, TipSerializer
from .models import Booking, BookingRejection
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
        vehicle_data = serializer.validated_data.get('vehicle_data')
        # If inline vehicle data provided, create a temporary object for pricing
        if not vehicle and vehicle_data:
            class _TmpVehicle:
                pass
            tmp = _TmpVehicle()
            tmp.vehicle_type = vehicle_data.get('vehicle_type')
            tmp.engine_type = vehicle_data.get('engine_type')
            vehicle_for_price = tmp
        else:
            vehicle_for_price = vehicle
        dirt_level = serializer.validated_data.get('dirt_level')
        # compute distance_km from booking coords or use provided value
        distance_km = serializer.validated_data.get('distance_km')
        try:
            distance_km = float(distance_km) if distance_km is not None else 0.0
        except Exception:
            distance_km = 0.0

        # If client didn't provide distance, attempt to estimate using nearest provider who offers the service
        service_lat = serializer.validated_data.get('service_latitude')
        service_lon = serializer.validated_data.get('service_longitude')
        if (not distance_km or distance_km == 0.0) and service_lat is not None and service_lon is not None and service is not None:
            try:
                from apps.providers.models import ProviderService
                offers_qs = ProviderService.objects.filter(
                    service=service,
                    is_active=True,
                    provider__status=ProviderProfile.STATUS_APPROVED,
                    provider__service_latitude__isnull=False,
                    provider__service_longitude__isnull=False,
                ).select_related('provider')
                min_dist = None
                for offer in offers_qs:
                    p = offer.provider
                    d = haversine_distance_km(p.service_latitude, p.service_longitude, service_lat, service_lon)
                    if min_dist is None or d < min_dist:
                        min_dist = d
                if min_dist is not None:
                    distance_km = float(min_dist)
            except Exception:
                # ignore and keep distance_km as provided or 0
                pass

        prices = calculate_booking_price(
            service=service,
            vehicle=vehicle_for_price,
            dirt_level=dirt_level,
            distance_km=distance_km,
        )

        booking = serializer.save(
            customer=profile,
            distance_km=distance_km,
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
        from decimal import Decimal
        
        profile = get_object_or_404(ProviderProfile, user=request.user)
        
        # Get available jobs (requested status, not yet assigned to any provider)
        jobs = Booking.objects.filter(
            status=Booking.STATUS_REQUESTED,
            provider__isnull=True
        ).exclude(
            # Exclude jobs that are "now" type and older than 5 minutes
            schedule_type=Booking.SCHEDULE_NOW,
            created_at__lt=timezone.now() - timedelta(minutes=5)
        ).order_by('-created_at')
        
        # Get rejected job IDs by this provider
        rejected_booking_ids = set(
            profile.job_rejections.values_list('booking_id', flat=True)
        )
        
        # Filter jobs by provider's service radius and exclude rejected jobs
        service_radius = Decimal(str(profile.service_radius_km))
        jobs = [
            job for job in jobs 
            if (Decimal(str(job.distance_km)) <= service_radius and 
                job.id not in rejected_booking_ids)
        ]
        
        data = JobListSerializer(
            jobs, many=True, context={'request': request}
        ).data
        return self.success_response(data=data)


class ProviderJobDetailView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        profile = get_object_or_404(ProviderProfile, user=request.user)
        from decimal import Decimal
        
        # Try to get the job - either an available job or a job assigned to this provider
        try:
            # First, check if it's one of the provider's own jobs
            job = Booking.objects.get(pk=pk, provider=profile)
        except Booking.DoesNotExist:
            # If not their own job, check if it's an available job they can view
            try:
                job = Booking.objects.get(
                    pk=pk, 
                    status=Booking.STATUS_REQUESTED,
                    provider__isnull=True
                )
                # Verify job is within provider's service radius
                service_radius = Decimal(str(profile.service_radius_km))
                if Decimal(str(job.distance_km)) > service_radius:
                    return self.error_response(
                        message="This job is outside your service radius."
                    )
            except Booking.DoesNotExist:
                return self.error_response(message="Job not found.")
        
        data = BookingDetailSerializer(job, context={'request': request}).data
        return self.success_response(data=data)


class ProviderJobAcceptView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        profile = get_object_or_404(ProviderProfile, user=request.user)
        booking = get_object_or_404(
            Booking, pk=pk, status=Booking.STATUS_REQUESTED
        )
        
        # Verify job is within provider's service radius
        from decimal import Decimal
        service_radius = Decimal(str(profile.service_radius_km))
        if Decimal(str(booking.distance_km)) > service_radius:
            return self.error_response(
                message="This job is outside your service radius."
            )
        
        # Check if provider has any active jobs
        active_statuses = [
            Booking.STATUS_ACCEPTED,
            Booking.STATUS_EN_ROUTE,
            Booking.STATUS_IN_PROGRESS,
        ]
        active_job = Booking.objects.filter(
            provider=profile,
            status__in=active_statuses
        ).exists()
        
        if active_job:
            return self.error_response(
                message="You have an active job. Please complete it before accepting another job."
            )
        
        booking.provider = profile
        booking.status = Booking.STATUS_ACCEPTED
        booking.accepted_at = timezone.now()
        booking.save()
        return self.success_response(message="Job accepted.")


class ProviderJobRejectView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        profile = get_object_or_404(ProviderProfile, user=request.user)
        booking = get_object_or_404(
            Booking, 
            pk=pk, 
            status=Booking.STATUS_REQUESTED,
            provider__isnull=True
        )
        
        # Create a rejection record to prevent showing this job to this provider again
        BookingRejection.objects.get_or_create(
            booking=booking,
            provider=profile
        )
        
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


class ProviderJobHistoryView(BaseResponseMixin, APIView):
    """
    Get provider's job history (accepted, active, completed, canceled jobs).
    
    Query Parameters:
    - status: Filter by status (accepted, en_route, in_progress, completed, cancelled)
    - type: 'active' (accepted/en_route/in_progress), 'completed', 'cancelled', or 'all' (default)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = get_object_or_404(ProviderProfile, user=request.user)
        
        # Get jobs assigned to this provider
        jobs = Booking.objects.filter(provider=profile).order_by('-created_at')
        
        # Filter by type if provided
        job_type = request.query_params.get('type', 'all').lower()
        if job_type == 'active':
            active_statuses = [
                Booking.STATUS_ACCEPTED,
                Booking.STATUS_EN_ROUTE,
                Booking.STATUS_IN_PROGRESS,
            ]
            jobs = jobs.filter(status__in=active_statuses)
        elif job_type == 'completed':
            jobs = jobs.filter(status=Booking.STATUS_COMPLETED)
        elif job_type == 'cancelled':
            jobs = jobs.filter(status=Booking.STATUS_CANCELLED)
        # 'all' returns all jobs assigned to provider
        
        # Filter by specific status if provided
        status_f = request.query_params.get('status')
        if status_f:
            jobs = jobs.filter(status=status_f)
        
        data = JobListSerializer(
            jobs, many=True, context={'request': request}
        ).data
        return self.success_response(data=data)
