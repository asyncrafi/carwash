from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.bookings.models import Booking
from apps.customers.models import CustomerProfile
from apps.payments.models import Payment, ProviderEarning
from apps.providers.models import ProviderProfile


class StripeModelFieldsTest(TestCase):
    def test_booking_has_stripe_payment_fields(self):
        booking_fields = {field.name for field in Booking._meta.get_fields()}

        self.assertIn('payment_status', booking_fields)
        self.assertIn('stripe_payment_intent_id', booking_fields)
        self.assertIn('stripe_transfer_id', booking_fields)

    def test_provider_has_stripe_onboarding_fields(self):
        provider_fields = {field.name for field in ProviderProfile._meta.get_fields()}

        self.assertIn('stripe_account_id', provider_fields)
        self.assertIn('stripe_onboarding_complete', provider_fields)

    def test_payment_status_includes_paid_and_released(self):
        self.assertIn(Payment.STATUS_PAID, [choice[0] for choice in Payment.STATUS_CHOICES])
        self.assertIn(Payment.STATUS_RELEASED, [choice[0] for choice in Payment.STATUS_CHOICES])


class StripeConnectFlowTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='provider@example.com',
            password='testpass123',
            full_name='Provider One',
        )
        self.provider = ProviderProfile.objects.create(user=self.user)
        self.customer_profile = CustomerProfile.objects.create(user=self.user)

    @patch('apps.payments.views.stripe.Account.create')
    @patch('apps.payments.views.stripe.AccountLink.create')
    def test_provider_can_start_stripe_connect_onboarding(self, mock_account_link, mock_account):
        mock_account.return_value = {'id': 'acct_123'}
        mock_account_link.return_value = {'url': 'https://connect.stripe.test/onboard'}

        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/payments/connect/onboard/', {}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['onboarding_url'], 'https://connect.stripe.test/onboard')
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.stripe_account_id, 'acct_123')

    @patch('apps.payments.views.stripe.Transfer.create')
    def test_release_payout_creates_transfer_for_completed_booking(self, mock_transfer):
        mock_transfer.return_value = {'id': 'tr_123'}
        booking = Booking.objects.create(
            customer=self.customer_profile,
            provider=self.provider,
            service_address='Test address',
            total_amount='100.00',
            status=Booking.STATUS_COMPLETED,
            payment_status=Booking.PAYMENT_STATUS_PAID,
            is_paid=True,
        )
        self.provider.stripe_account_id = 'acct_123'
        self.provider.stripe_onboarding_complete = True
        self.provider.save(update_fields=['stripe_account_id', 'stripe_onboarding_complete'])
        ProviderEarning.objects.create(
            provider=self.provider,
            booking=booking,
            gross_amount='100.00',
            platform_fee='10.00',
            net_amount='90.00',
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/payments/release-payout/', {'booking_id': booking.id}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(ProviderEarning.objects.get(booking=booking).is_paid_out)
        self.assertEqual(mock_transfer.call_count, 1)
