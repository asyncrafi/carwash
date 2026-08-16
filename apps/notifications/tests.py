from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

User = get_user_model()


class NotificationApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            username='user',
            password='StrongPass123',
            full_name='Test User',
            role='customer',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_register_fcm_token(self):
        url = reverse('notifications:fcm-token')
        response = self.client.post(
            url,
            {'token': 'abc-123-fcm-token', 'device_type': 'android'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['token'], 'abc-123-fcm-token')

    def test_list_fcm_tokens(self):
        self.user.fcm_tokens.create(token='abc-123', device_type='android', is_active=True)
        self.user.fcm_tokens.create(token='def-456', device_type='ios', is_active=True)

        response = self.client.get(reverse('notifications:fcm-token'))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']), 2)

    def test_update_notification_preferences(self):
        url = reverse('notifications:preferences')
        response = self.client.patch(
            url,
            {'push_enabled': False, 'in_app_enabled': True, 'email_enabled': False},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertFalse(response.data['data']['push_enabled'])
        self.assertFalse(response.data['data']['email_enabled'])

    def test_method_not_allowed_returns_405_without_crashing(self):
        url = reverse('notifications:fcm-token')
        response = self.client.put(url, {'token': 'abc'}, format='json')

        self.assertEqual(response.status_code, 405)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error_code'], 'METHOD_NOT_ALLOWED')
        self.assertIn('not allowed', response.data['message'].lower())
