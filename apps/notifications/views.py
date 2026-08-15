from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers

from apps.core.mixins import BaseResponseMixin
from .models import FCMToken, Notification, UserNotificationPreference
from .serializers import NotificationSerializer


class FCMTokenRegisterSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=255)
    device_type = serializers.ChoiceField(choices=['android', 'ios', 'web'], required=False, default='android')


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNotificationPreference
        fields = ['push_enabled', 'in_app_enabled', 'email_enabled']


class FCMTokenRegisterView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tokens = FCMToken.objects.filter(user=request.user, is_active=True)
        data = [{
            'id': token.id,
            'token': token.token,
            'device_type': token.device_type,
            'is_active': token.is_active,
            'updated_at': token.updated_at,
        } for token in tokens]
        return self.success_response(data=data)

    def post(self, request):
        serializer = FCMTokenRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data['token']
        device_type = serializer.validated_data.get('device_type', 'android')

        obj, created = FCMToken.objects.update_or_create(
            user=request.user,
            token=token,
            defaults={'device_type': device_type, 'is_active': True},
        )

        return self.success_response(
            data={
                'id': obj.id,
                'token': obj.token,
                'device_type': obj.device_type,
                'is_active': obj.is_active,
                'created': created,
            },
            message='FCM token registered successfully.',
        )

    def delete(self, request):
        token = request.data.get('token')
        if not token:
            return self.bad_request_response(message='Token is required.')

        deleted, _ = FCMToken.objects.filter(user=request.user, token=token).delete()
        if deleted == 0:
            return self.not_found_response(message='FCM token not found.')

        return self.success_response(message='FCM token removed successfully.')


class NotificationPreferencesView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        pref, created = UserNotificationPreference.objects.get_or_create(user=request.user)
        return self.success_response(data=NotificationPreferenceSerializer(pref).data)

    def patch(self, request):
        pref, created = UserNotificationPreference.objects.get_or_create(user=request.user)
        serializer = NotificationPreferenceSerializer(pref, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.success_response(
            data=serializer.data,
            message='Notification preferences updated successfully.',
        )


class NotificationListView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(user=request.user)
        data = NotificationSerializer(notifications, many=True).data
        return self.success_response(data=data)


class NotificationMarkReadView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        notif = get_object_or_404(Notification, pk=pk, user=request.user)
        notif.is_read = True
        notif.save()
        return self.success_response(message="Notification marked as read.")


class NotificationMarkAllReadView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        Notification.objects.filter(
            user=request.user, is_read=False
        ).update(is_read=True)
        return self.success_response(
            message="All notifications marked as read."
        )
