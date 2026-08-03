from django.test import TestCase

from apps.bookings.models import Booking
from apps.payments.models import Payment
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
