from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch
from rest_framework.test import APIClient

from apps.providers.models import ProviderProfile
from apps.bookings.models import Booking


class ProviderOnboardingGateTests(TestCase):
    def setUp(self):
        self.client = APIClient()
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

        self.client.force_authenticate(user=self.user)
        response = self.client.patch('/api/provider/online-status/', {'is_online': True}, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['error_code'], 'STRIPE_ONBOARDING_REQUIRED')
        self.assertIn('Complete your Stripe payout setup before you can go online.', response.json()['message'])

    @patch('apps.providers.views.stripe.Account.create')
    @patch('apps.providers.views.stripe.AccountLink.create')
    def test_provider_account_link_auto_heals_mismatch(self, mock_account_link, mock_account):
        import stripe
        self.profile.stripe_account_id = 'acct_old_test'
        self.profile.save(update_fields=['stripe_account_id'])

        mismatch_err = stripe.error.InvalidRequestError(
            message='You tried to create a live mode account link for an account that was created in test mode.',
            param=None,
            code=None,
        )
        mock_account.return_value = {'id': 'acct_new_live'}
        mock_account_link.side_effect = [
            mismatch_err,
            {'url': 'https://stripe.test/new_link'},
        ]

        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/provider/stripe/account-link/', {}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['account_id'], 'acct_new_live')
        self.assertEqual(response.json()['data']['url'], 'https://stripe.test/new_link')
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.stripe_account_id, 'acct_new_live')
