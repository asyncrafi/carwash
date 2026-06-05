from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser

from apps.core.mixins import BaseResponseMixin
from apps.accounts.models import User
from apps.customers.models import CustomerProfile
from apps.providers.models import ProviderProfile, ProviderDocument
from apps.bookings.models import Booking
from apps.payments.models import Payment, ProviderEarning
from apps.services.models import Service, PlatformConfig
from apps.notifications.tasks import bulk_create_notifications_task
from apps.providers.serializers import ProviderDocumentSerializer
from apps.bookings.serializers import BookingListSerializer, BookingDetailSerializer
from apps.payments.serializers import ProviderEarningSerializer
from apps.services.serializers import ServiceSerializer, PlatformConfigSerializer


class AdminDashboardView(BaseResponseMixin, APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        now = timezone.now()

        total_orders = Booking.objects.count()
        total_providers = ProviderProfile.objects.count()
        total_customers = CustomerProfile.objects.count()
        total_revenue = Payment.objects.filter(status='success').aggregate(
            total=Sum('amount')
        )['total'] or 0
        total_commission = ProviderEarning.objects.aggregate(
            total=Sum('platform_fee')
        )['total'] or 0

        revenue_chart = (
            Payment.objects
            .filter(status='success')
            .annotate(month=TruncMonth('paid_at'))
            .values('month')
            .annotate(total=Sum('amount'))
            .order_by('month')
        )

        top_providers = (
            ProviderProfile.objects
            .filter(
                jobs__status='completed',
                jobs__completed_at__month=now.month,
            )
            .annotate(job_count=Count('jobs'))
            .order_by('-job_count')[:5]
        )

        top_services = (
            Service.objects
            .annotate(booking_count=Count('booking'))
            .order_by('-booking_count')[:5]
        )

        recent = Booking.objects.select_related(
            'customer__user', 'provider__user', 'service'
        ).order_by('-created_at')[:10]

        top_provider_data = []
        for p in top_providers:
            top_provider_data.append({
                'id': p.id,
                'name': p.user.get_full_name(),
                'avatar': (
                    request.build_absolute_uri(p.user.avatar.url)
                    if p.user.avatar else None
                ),
                'rating': float(p.average_rating),
                'total_washes': p.total_washes,
            })

        top_service_data = []
        for s in top_services:
            top_service_data.append({
                'id': s.id,
                'name': s.name,
                'booking_count': s.booking_count,
            })

        recent_data = []
        for b in recent:
            recent_data.append({
                'id': b.id,
                'customer': b.customer.user.get_full_name(),
                'provider': (
                    b.provider.user.get_full_name() if b.provider else None
                ),
                'service': b.service.name if b.service else None,
                'status': b.status,
                'total_amount': float(b.total_amount),
                'created_at': b.created_at,
            })

        data = {
            'stats': {
                'total_orders': total_orders,
                'total_providers': total_providers,
                'total_customers': total_customers,
                'total_revenue': float(total_revenue),
                'total_commission': float(total_commission),
            },
            'revenue_chart': list(revenue_chart),
            'top_providers': top_provider_data,
            'top_services': top_service_data,
            'recent_activity': recent_data,
        }
        return self.success_response(data=data)


class AdminUserListView(BaseResponseMixin, APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        role = request.query_params.get('role')
        user_status = request.query_params.get('status')
        search = request.query_params.get('search', '')

        qs = User.objects.exclude(is_superuser=True)
        if role:
            qs = qs.filter(role=role)
        if search:
            qs = qs.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search)
            )
        if user_status == 'active':
            qs = qs.filter(is_active=True)
        elif user_status == 'blocked':
            qs = qs.filter(is_active=False)
        elif user_status == 'pending':
            provider_ids = ProviderProfile.objects.filter(
                status='pending'
            ).values_list('user_id', flat=True)
            qs = qs.filter(id__in=provider_ids)

        data = []
        for u in qs.order_by('-date_joined'):
            entry = {
                'id': u.id,
                'full_name': u.get_full_name(),
                'email': u.email,
                'phone': u.phone,
                'role': u.role,
                'is_active': u.is_active,
                'is_verified': u.is_verified,
                'avatar': (
                    request.build_absolute_uri(u.avatar.url)
                    if u.avatar else None
                ),
                'joined_at': u.date_joined,
            }
            if u.role == 'provider' and hasattr(u, 'provider_profile'):
                p = u.provider_profile
                entry.update({
                    'provider_status': p.status,
                    'average_rating': float(p.average_rating),
                    'total_washes': p.total_washes,
                    'total_earnings': float(
                        ProviderEarning.objects.filter(provider=p)
                        .aggregate(t=Sum('net_amount'))['t'] or 0
                    ),
                })
            data.append(entry)

        return self.success_response(data=data)


class AdminUserDetailView(BaseResponseMixin, APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        from apps.accounts.serializers import UserSerializer
        data = UserSerializer(user).data
        if user.role == 'provider' and hasattr(user, 'provider_profile'):
            p = user.provider_profile
            from apps.providers.serializers import ProviderProfileSerializer
            data['provider_profile'] = ProviderProfileSerializer(p).data
            data['stats'] = {
                'completed_jobs': Booking.objects.filter(
                    provider=p, status='completed'
                ).count(),
                'total_earnings': float(
                    ProviderEarning.objects.filter(provider=p)
                    .aggregate(t=Sum('net_amount'))['t'] or 0
                ),
                'average_rating': float(p.average_rating),
                'approved_docs': ProviderDocument.objects.filter(
                    provider=p, status='approved'
                ).count(),
                'total_docs': ProviderDocument.objects.filter(
                    provider=p
                ).count(),
            }
        return self.success_response(data=data)

    def patch(self, request, pk):
        from apps.accounts.serializers import UserSerializer
        user = get_object_or_404(User, pk=pk)
        serializer = UserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.updated_response(data=serializer.data)


class AdminUserBlockView(BaseResponseMixin, APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.is_active = False
        user.save()
        return self.success_response(
            message=f"User {user.get_full_name()} blocked successfully."
        )


class AdminUserUnblockView(BaseResponseMixin, APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.is_active = True
        user.save()
        return self.success_response(
            message=f"User {user.get_full_name()} unblocked successfully."
        )


class AdminProviderDocumentListView(BaseResponseMixin, APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, provider_pk):
        provider = get_object_or_404(ProviderProfile, pk=provider_pk)
        docs = ProviderDocument.objects.filter(provider=provider)
        data = ProviderDocumentSerializer(docs, many=True).data
        return self.success_response(data=data)


class AdminDocumentReviewView(BaseResponseMixin, APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, pk):
        doc = get_object_or_404(ProviderDocument, pk=pk)
        new_st = request.data.get('status')
        note = request.data.get('admin_note', '')
        if new_st not in ['approved', 'rejected']:
            return self.bad_request_response(
                message="Status must be approved or rejected."
            )
        doc.status = new_st
        doc.admin_note = note
        doc.reviewed_at = timezone.now()
        doc.save()
        return self.updated_response(
            data=ProviderDocumentSerializer(doc).data,
            message="Document status reviewed.",
        )


class AdminProviderApproveView(BaseResponseMixin, APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        provider = get_object_or_404(ProviderProfile, pk=pk)
        provider.status = 'approved'
        provider.save()
        return self.success_response(
            message=f"Provider {provider.user.get_full_name()} approved."
        )


class AdminProviderRejectView(BaseResponseMixin, APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        provider = get_object_or_404(ProviderProfile, pk=pk)
        provider.status = 'rejected'
        provider.save()
        return self.success_response(
            message=f"Provider {provider.user.get_full_name()} rejected."
        )


class AdminBookingListView(BaseResponseMixin, APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        qs = Booking.objects.select_related(
            'customer__user', 'provider__user', 'service'
        ).order_by('-created_at')
        st = request.query_params.get('status')
        search = request.query_params.get('search', '')
        if st:
            qs = qs.filter(status=st)
        if search:
            qs = qs.filter(
                Q(customer__user__first_name__icontains=search) |
                Q(customer__user__last_name__icontains=search) |
                Q(provider__user__first_name__icontains=search) |
                Q(service__name__icontains=search)
            )
        data = BookingListSerializer(
            qs, many=True, context={'request': request}
        ).data
        return self.success_response(data=data)


class AdminBookingDetailView(BaseResponseMixin, APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)
        data = BookingDetailSerializer(
            booking, context={'request': request}
        ).data
        return self.success_response(data=data)


class AdminBookingCancelView(BaseResponseMixin, APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)
        if booking.status in ['completed', 'cancelled']:
            return self.bad_request_response(
                message="Cannot cancel this booking."
            )
        booking.status = 'cancelled'
        booking.cancelled_at = timezone.now()
        booking.cancel_reason = request.data.get(
            'cancel_reason', 'Cancelled by admin.'
        )
        booking.save()
        return self.success_response(message="Booking cancelled successfully.")


class AdminEarningsDashboardView(BaseResponseMixin, APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        earnings = ProviderEarning.objects.select_related(
            'provider__user', 'booking__service'
        ).order_by('-created_at')

        total_revenue = Payment.objects.filter(status='success').aggregate(
            t=Sum('amount')
        )['t'] or 0
        total_commission = earnings.aggregate(
            t=Sum('platform_fee')
        )['t'] or 0
        accrued_balance = earnings.filter(is_paid_out=False).aggregate(
            t=Sum('net_amount')
        )['t'] or 0

        config = PlatformConfig.objects.first()

        chart_data = (
            earnings
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(
                earnings_total=Sum('net_amount'),
                revenue_total=Sum('gross_amount'),
            )
            .order_by('month')
        )

        table_data = []
        for e in earnings[:50]:
            table_data.append({
                'id': e.id,
                'provider': e.provider.user.get_full_name(),
                'customer': e.booking.customer.user.get_full_name(),
                'service': (
                    e.booking.service.name if e.booking.service else ''
                ),
                'gross_amount': float(e.gross_amount),
                'commission': float(e.platform_fee),
                'net_amount': float(e.net_amount),
                'status': 'paid' if e.is_paid_out else 'pending',
                'created_at': e.created_at,
            })

        data = {
            'stats': {
                'total_revenue': float(total_revenue),
                'total_commission': float(total_commission),
                'accrued_balance': float(accrued_balance),
                'platform_fee_pct': (
                    float(config.commission_percent) if config else 15
                ),
            },
            'chart_data': list(chart_data),
            'earnings': table_data,
        }
        return self.success_response(data=data)


class AdminPayoutsListView(BaseResponseMixin, APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        qs = ProviderEarning.objects.select_related(
            'provider__user', 'booking'
        ).order_by('-created_at')
        st = request.query_params.get('status')
        if st == 'paid':
            qs = qs.filter(is_paid_out=True)
        elif st == 'pending':
            qs = qs.filter(is_paid_out=False)
        data = ProviderEarningSerializer(qs, many=True).data
        return self.success_response(data=data)


class AdminPayoutRetryView(BaseResponseMixin, APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        earning = get_object_or_404(
            ProviderEarning, pk=pk, is_paid_out=False
        )
        earning.is_paid_out = True
        earning.paid_out_at = timezone.now()
        earning.save()
        return self.success_response(message="Payout marked as completed.")


class AdminServiceListCreateView(BaseResponseMixin, APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        qs = Service.objects.all().order_by('order')
        data = ServiceSerializer(qs, many=True).data
        return self.success_response(data=data)

    def post(self, request):
        serializer = ServiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.created_response(
            data=serializer.data, message="Service created successfully."
        )


class AdminServiceDetailView(BaseResponseMixin, APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        data = ServiceSerializer(
            get_object_or_404(Service, pk=pk)
        ).data
        return self.success_response(data=data)

    def patch(self, request, pk):
        service = get_object_or_404(Service, pk=pk)
        serializer = ServiceSerializer(
            service, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.updated_response(
            data=serializer.data, message="Service updated successfully."
        )

    def delete(self, request, pk):
        get_object_or_404(Service, pk=pk).delete()
        return self.deleted_response(message="Service deleted successfully.")


class AdminPlatformConfigView(BaseResponseMixin, APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        config, _ = PlatformConfig.objects.get_or_create(pk=1)
        data = PlatformConfigSerializer(config).data
        return self.success_response(data=data)

    def patch(self, request):
        config, _ = PlatformConfig.objects.get_or_create(pk=1)
        serializer = PlatformConfigSerializer(
            config, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.updated_response(
            data=serializer.data,
            message="Platform configuration updated.",
        )


class AdminSendNotificationView(BaseResponseMixin, APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        target = request.data.get('target', 'all')
        title = request.data.get('title', '')
        body = request.data.get('body', '')
        if not title or not body:
            return self.bad_request_response(
                message="Title and body are required."
            )
        qs = User.objects.exclude(is_superuser=True)
        if target == 'customers':
            qs = qs.filter(role='customer')
        elif target == 'providers':
            qs = qs.filter(role='provider')

        user_ids = list(qs.values_list('id', flat=True))
        if user_ids:
            bulk_create_notifications_task.delay(
                user_ids=user_ids,
                notif_type='general',
                title=title,
                body=body,
            )
        return self.success_response(
            message=f"Notification queued for {len(user_ids)} users."
        )
