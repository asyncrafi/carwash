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


class PaidOnlyBookingDispatchTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        User = get_user_model()
        self.provider_user = User.objects.create_user(
            email='provider2@example.com',
            password='testpass123',
            full_name='Provider Two',
        )
        self.provider = ProviderProfile.objects.create(
            user=self.provider_user,
            status=ProviderProfile.STATUS_APPROVED,
            stripe_account_id='acct_provider_2',
            stripe_onboarding_complete=True,
            service_radius_km=50.0,
        )
        self.customer_user = User.objects.create_user(
            email='customer@example.com',
            password='testpass123',
            full_name='Customer Test',
        )
        self.customer = CustomerProfile.objects.create(user=self.customer_user)

    def test_unpaid_booking_hidden_from_provider_job_list(self):
        # Create an unpaid booking
        unpaid_booking = Booking.objects.create(
            customer=self.customer,
            service_address='123 Unpaid St',
            total_amount='50.00',
            distance_km=5.0,
            status=Booking.STATUS_REQUESTED,
            payment_status=Booking.PAYMENT_STATUS_PENDING,
            is_paid=False,
        )
        # Create a paid booking
        paid_booking = Booking.objects.create(
            customer=self.customer,
            service_address='456 Paid St',
            total_amount='60.00',
            distance_km=5.0,
            status=Booking.STATUS_REQUESTED,
            payment_status=Booking.PAYMENT_STATUS_PAID,
            is_paid=True,
        )

        self.client.force_authenticate(user=self.provider_user)
        response = self.client.get('/api/bookings/provider/jobs/')

        self.assertEqual(response.status_code, 200)
        job_ids = [job['id'] for job in response.data['data']]
        self.assertNotIn(unpaid_booking.id, job_ids)
        self.assertIn(paid_booking.id, job_ids)

    def test_provider_cannot_accept_unpaid_booking(self):
        unpaid_booking = Booking.objects.create(
            customer=self.customer,
            service_address='123 Unpaid St',
            total_amount='50.00',
            distance_km=5.0,
            status=Booking.STATUS_REQUESTED,
            payment_status=Booking.PAYMENT_STATUS_PENDING,
            is_paid=False,
        )

        self.client.force_authenticate(user=self.provider_user)
        response = self.client.post(f'/api/bookings/provider/jobs/{unpaid_booking.id}/accept/')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data.get('error_code'), 'PAYMENT_PENDING')
        unpaid_booking.refresh_from_db()
        self.assertIsNone(unpaid_booking.provider)

    @patch('apps.bookings.tasks.handle_booking_created.delay')
    def test_stripe_webhook_succeeded_dispatches_booking(self, mock_handle_booking_created):
        booking = Booking.objects.create(
            customer=self.customer,
            service_address='123 Pending St',
            total_amount='70.00',
            distance_km=5.0,
            status=Booking.STATUS_REQUESTED,
            payment_status=Booking.PAYMENT_STATUS_PENDING,
            stripe_payment_intent_id='pi_test_12345',
            is_paid=False,
        )

        with patch('apps.payments.views.settings') as mock_settings:
            mock_settings.STRIPE_WEBHOOK_SECRET = 'whsec_test'
            with patch('apps.payments.views.stripe.Webhook.construct_event') as mock_construct:
                mock_construct.return_value = {
                    'type': 'payment_intent.succeeded',
                    'data': {
                        'object': {
                            'id': 'pi_test_12345',
                        }
                    }
                }
                response = self.client.post(
                    '/api/payments/stripe/webhook/',
                    data='dummy payload',
                    content_type='application/json',
                    HTTP_STRIPE_SIGNATURE='t=123,v1=abc',
                )

        self.assertEqual(response.status_code, 200)
        booking.refresh_from_db()
        self.assertTrue(booking.is_paid)
        self.assertEqual(booking.payment_status, Booking.PAYMENT_STATUS_PAID)
        self.assertTrue(mock_handle_booking_created.called)

    @patch('apps.bookings.tasks.handle_booking_created.delay')
    @patch('apps.payments.views.stripe.PaymentIntent.retrieve')
    def test_confirm_payment_endpoint_verifies_and_dispatches(self, mock_retrieve, mock_handle_booking_created):
        mock_retrieve.return_value = {'id': 'pi_confirm_123', 'status': 'succeeded'}

        booking = Booking.objects.create(
            customer=self.customer,
            service_address='789 Confirm St',
            total_amount='85.00',
            distance_km=5.0,
            status=Booking.STATUS_REQUESTED,
            payment_status=Booking.PAYMENT_STATUS_PENDING,
            stripe_payment_intent_id='pi_confirm_123',
            is_paid=False,
        )

        with patch('apps.payments.views.settings') as mock_settings:
            mock_settings.STRIPE_SECRET_KEY = 'sk_test_key'
            self.client.force_authenticate(user=self.customer_user)
            response = self.client.post(
                '/api/payments/confirm-payment/',
                {'booking_id': booking.id},
                format='json',
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['payment_status'], 'paid')
        self.assertTrue(response.data['data']['is_paid'])
        booking.refresh_from_db()
        self.assertTrue(booking.is_paid)
        self.assertEqual(booking.payment_status, Booking.PAYMENT_STATUS_PAID)
        self.assertTrue(mock_handle_booking_created.called)


