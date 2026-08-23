from decimal import Decimal

import stripe
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny

from apps.core.mixins import BaseResponseMixin
from apps.providers.models import ProviderProfile
from apps.bookings.models import Booking
from apps.core.utils import calculate_provider_earning
from .models import Payment, ProviderEarning
from .serializers import ProviderEarningSerializer
from .utils import create_provider_earning

# Initialize Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY


def get_stripe_val(obj, key, default=None):
    if obj is None:
        return default
    if hasattr(obj, key):
        val = getattr(obj, key)
        if val is not None:
            return val
    if isinstance(obj, dict):
        return obj.get(key, default)
    if hasattr(obj, 'get'):
        try:
            return obj.get(key, default)
        except (AttributeError, TypeError):
            pass
    if hasattr(obj, '__getitem__'):
        try:
            return obj[key]
        except (KeyError, TypeError, IndexError):
            pass
    return default


class StripeWebhookView(BaseResponseMixin, APIView):
    permission_classes = [AllowAny]

    @csrf_exempt
    def post(self, request):
        if not settings.STRIPE_WEBHOOK_SECRET:
            return self.error_response(
                message='Stripe webhook secret is not configured.',
                error_code='STRIPE_WEBHOOK_NOT_CONFIGURED',
                status_code=500,
            )

        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            return self.error_response(message='Invalid Stripe payload.', status_code=400)
        except stripe.error.SignatureVerificationError:
            return self.error_response(message='Invalid Stripe signature.', status_code=400)

        event_type = get_stripe_val(event, 'type')
        data_obj = get_stripe_val(event, 'data', {})
        obj = get_stripe_val(data_obj, 'object', {}) if data_obj else {}

        if event_type == 'account.updated':
            account_id = get_stripe_val(obj, 'id')
            provider = get_object_or_404(ProviderProfile, stripe_account_id=account_id)
            account = stripe.Account.retrieve(account_id)
            details_submitted = get_stripe_val(account, 'details_submitted', False)
            payouts_enabled = get_stripe_val(account, 'payouts_enabled', False)
            provider.stripe_onboarding_complete = bool(details_submitted and payouts_enabled)
            provider.save(update_fields=['stripe_onboarding_complete'])
            return self.success_response(message='Provider onboarding status updated.')

        if event_type == 'payment_intent.succeeded':
            payment_intent_id = get_stripe_val(obj, 'id')
            booking = Booking.objects.filter(
                stripe_payment_intent_id=payment_intent_id
            ).select_related('customer__user', 'provider__user').first()
            if not booking:
                return self.success_response(message='PaymentIntent succeeded but no booking matched.')

            booking.payment_status = Booking.PAYMENT_STATUS_PAID
            booking.is_paid = True
            booking.save(update_fields=['payment_status', 'is_paid'])

            Payment.objects.update_or_create(
                booking=booking,
                defaults={
                    'amount': booking.total_amount,
                    'currency': 'eur',
                    'status': Payment.STATUS_PAID,
                    'gateway': 'stripe',
                    'transaction_id': payment_intent_id,
                    'paid_at': timezone.now(),
                },
            )
            return self.success_response(message='Booking marked as paid via Stripe.')

        return self.success_response(message=f'Unhandled Stripe event: {event_type}')


class CreatePaymentIntentView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        booking_id = request.data.get('booking_id')
        if not booking_id:
            return self.bad_request_response(message='booking_id is required.')

        booking = get_object_or_404(Booking, pk=booking_id, customer__user=request.user)
        if booking.payment_status == Booking.PAYMENT_STATUS_PAID:
            return self.error_response(message='This booking has already been paid.', status_code=409)

        if not settings.STRIPE_SECRET_KEY:
            return self.error_response(
                message='Stripe secret key is not configured.',
                error_code='STRIPE_NOT_CONFIGURED',
            )

        amount_cents = int((Decimal(str(booking.total_amount)) * 100).to_integral_value())
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency='eur',
            automatic_payment_methods={'enabled': True},
            metadata={'booking_id': str(booking.id), 'customer_id': str(request.user.id)},
        )

        intent_id = get_stripe_val(intent, 'id')
        client_secret = get_stripe_val(intent, 'client_secret')

        booking.stripe_payment_intent_id = intent_id
        booking.payment_status = Booking.PAYMENT_STATUS_PENDING
        booking.save(update_fields=['stripe_payment_intent_id', 'payment_status'])

        return self.success_response(
            data={
                'client_secret': client_secret,
                'payment_intent_id': intent_id,
                'booking_id': booking.id,
                'amount': str(booking.total_amount),
                'currency': 'eur',
                'payment_status': booking.payment_status,
            },
            message='Stripe PaymentIntent created successfully.',
        )


class ConnectOnboardingView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not settings.STRIPE_SECRET_KEY:
            return self.error_response(
                message='Stripe secret key is not configured.',
                error_code='STRIPE_NOT_CONFIGURED',
            )

        profile, _ = ProviderProfile.objects.get_or_create(user=request.user)

        account_id = profile.stripe_account_id
        try:
            if not account_id:
                account = stripe.Account.create(
                    type='standard',
                    email=request.user.email,
                    metadata={'user_id': str(request.user.id)},
                )
                account_id = get_stripe_val(account, 'id')
                profile.stripe_account_id = account_id
                profile.save(update_fields=['stripe_account_id'])

            return_url = request.build_absolute_uri('/api/health/')
            refresh_url = request.build_absolute_uri('/api/health/')
            account_link = stripe.AccountLink.create(
                account=account_id,
                refresh_url=refresh_url,
                return_url=return_url,
                type='account_onboarding',
            )
            onboarding_url = get_stripe_val(account_link, 'url')
        except stripe.error.StripeError as e:
            error_msg = getattr(e, 'user_message', None)
            if not error_msg and hasattr(e, 'error') and e.error and getattr(e.error, 'message', None):
                error_msg = e.error.message
            if not error_msg:
                error_msg = str(e)
            return self.error_response(
                message=error_msg,
                error_code=getattr(e, 'code', 'STRIPE_ERROR') or 'STRIPE_ERROR',
                status_code=400,
            )

        return self.success_response(
            data={
                'account_id': account_id,
                'onboarding_url': onboarding_url,
                'onboarding_complete': profile.stripe_onboarding_complete,
            },
            message='Stripe Connect onboarding link created successfully.',
        )


class ReleasePayoutView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        booking_id = request.data.get('booking_id')
        if not booking_id:
            return self.bad_request_response(message='booking_id is required.')

        profile = get_object_or_404(ProviderProfile, user=request.user)
        booking = get_object_or_404(Booking, pk=booking_id, provider=profile)

        if booking.status != Booking.STATUS_COMPLETED:
            return self.error_response(
                message='Only completed bookings can be paid out.',
                error_code='INVALID_BOOKING_STATUS',
            )

        if booking.payment_status == Booking.PAYMENT_STATUS_RELEASED:
            return self.error_response(message='This payout has already been released.', status_code=409)

        if booking.payment_status != Booking.PAYMENT_STATUS_PAID:
            return self.error_response(
                message='Payment must be captured before the provider can be paid.',
                error_code='PAYMENT_NOT_PAID',
            )

        if not profile.stripe_account_id:
            return self.error_response(
                message='Provider is not connected to Stripe.',
                error_code='PROVIDER_NOT_CONNECTED',
            )

        earning = None
        try:
            earning = booking.earning
        except Exception:
            earning = None

        if earning is None:
            create_provider_earning(booking)
            try:
                earning = booking.earning
            except Exception:
                earning = None

        if earning is None:
            breakdown = calculate_provider_earning(booking)
            earning = ProviderEarning.objects.create(
                provider=profile,
                booking=booking,
                gross_amount=breakdown['gross_amount'],
                platform_fee=breakdown['platform_fee'],
                net_amount=breakdown['net_amount'],
            )

        transfer = stripe.Transfer.create(
            amount=int((Decimal(str(earning.net_amount)) * 100).to_integral_value()),
            currency='eur',
            destination=profile.stripe_account_id,
            metadata={'booking_id': str(booking.id), 'provider_id': str(profile.id)},
        )

        transfer_id = get_stripe_val(transfer, 'id')

        earning.stripe_transfer_id = transfer_id
        earning.is_paid_out = True
        earning.paid_out_at = timezone.now()
        earning.save(update_fields=['stripe_transfer_id', 'is_paid_out', 'paid_out_at'])

        booking.stripe_transfer_id = transfer_id
        booking.payment_status = Booking.PAYMENT_STATUS_RELEASED
        booking.save(update_fields=['stripe_transfer_id', 'payment_status'])

        return self.success_response(
            data={
                'booking_id': booking.id,
                'transfer_id': transfer_id,
                'provider_amount': str(earning.net_amount),
                'payment_status': booking.payment_status,
            },
            message='Provider payout transferred successfully.',
        )


class ProviderEarningsView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = get_object_or_404(ProviderProfile, user=request.user)
        earnings = ProviderEarning.objects.filter(
            provider=profile
        ).order_by('-created_at')
        total = earnings.aggregate(
            total=Sum('net_amount')
        )['total'] or 0
        today = earnings.filter(
            created_at__date=timezone.now().date()
        ).aggregate(today=Sum('net_amount'))['today'] or 0
        jobs_total = earnings.count()

        data = {
            'total_balance': float(total),
            'today_earnings': float(today),
            'jobs_total': jobs_total,
            'earnings': ProviderEarningSerializer(earnings, many=True).data,
        }
        return self.success_response(data=data)
