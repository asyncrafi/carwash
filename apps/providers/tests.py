from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch

from apps.providers.models import ProviderProfile
from apps.bookings.models import Booking


class ProviderOnboardingGateTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='provider@example.com',
            username='provider@example.com',
            password='secret123',
            role='provider',
            full_name='Test Provider',
        )
        self.profile = ProviderProfile.objects.create(user=self.user)

    @patch('apps.providers.views.stripe.Account.create')
    @patch('apps.providers.views.stripe.Account.retrieve')
    @patch('apps.providers.views.stripe.AccountLink.create')
    def test_provider_cannot_go_online_until_onboarding_is_complete(
        self, mock_account_link_create, mock_account_retrieve, mock_account_create
    ):
        mock_account_create.return_value = {'id': 'acct_test123'}
        mock_account_retrieve.return_value = {
            'id': 'acct_test123',
            'details_submitted': True,
            'payouts_enabled': False,
        }
        mock_account_link_create.return_value = {'url': 'https://stripe.test/onboard'}

        self.client.force_login(self.user)
        response = self.client.patch('/api/providers/online-status/', {'is_online': True}, content_type='application/json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['error_code'], 'STRIPE_ONBOARDING_REQUIRED')
        self.assertIn('Complete your Stripe payout setup before you can go online.', response.json()['message'])
