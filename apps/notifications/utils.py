from django.contrib.auth import get_user_model

from .models import FCMToken, Notification
from .tasks import (
    create_notification_task,
    notify_all_online_providers_task,
    send_push_notification_task,
    send_websocket_notification_task,
)


class NotificationService:
    @staticmethod
    def send_notification(user_id, title, message, notification_types=None, data=None):
        user = get_user_model().objects.get(id=user_id)
        notification_types = notification_types or ['push']
        for notif_type in notification_types:
            if notif_type == 'push':
                notify_user(user, Notification.TYPE_GENERAL, title, message, data=data, send_push=True, send_websocket=False)
            elif notif_type == 'in_app':
                notify_user(user, Notification.TYPE_GENERAL, title, message, data=data, send_push=False, send_websocket=True)
            else:
                notify_user(user, Notification.TYPE_GENERAL, title, message, data=data, send_push=False, send_websocket=False)

    @staticmethod
    def register_device_token(user, token, device_type='android'):
        obj, _ = FCMToken.objects.update_or_create(
            user=user,
            token=token,
            defaults={'device_type': device_type, 'is_active': True},
        )
        return obj


def notify_user(user, notif_type, title, body, data=None, send_push=True, send_websocket=True):
    notification = Notification.objects.create(
        user=user,
        notif_type=notif_type,
        title=title,
        body=body,
        data=data or {},
    )
    if send_push:
        send_push_notification_task.delay(notification.id)
    if send_websocket:
        send_websocket_notification_task.delay(notification.id)
    return notification


def notify_all_online_providers(booking):
    notify_all_online_providers_task.delay(
        booking_id=booking.id,
        service_name=booking.service.name if booking.service else None,
        service_city=booking.service_city,
        service_address=booking.service_address,
        total_amount=str(booking.total_amount),
        distance_km=str(booking.distance_km),
        service_latitude=getattr(booking, 'service_latitude', None),
        service_longitude=getattr(booking, 'service_longitude', None),
    )
