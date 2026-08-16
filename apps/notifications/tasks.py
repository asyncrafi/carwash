import logging

from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import FCMToken, Notification
from apps.providers.models import ProviderProfile, ProviderService
from apps.core.utils import haversine_distance_km

logger = logging.getLogger(__name__)

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
except Exception:
    firebase_admin = None
    credentials = None
    messaging = None

if firebase_admin is not None and not firebase_admin._apps:
    credentials_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', '')
    if credentials_path:
        try:
            cred = credentials.Certificate(credentials_path)
            firebase_admin.initialize_app(cred)
        except Exception as exc:
            logger.warning(f"Firebase initialization skipped: {exc}")


@shared_task
def create_notification_task(user_id, notif_type, title, body, data=None):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
        Notification.objects.create(
            user=user,
            notif_type=notif_type,
            title=title,
            body=body,
            data=data or {},
        )
    except User.DoesNotExist:
        logger.warning(f"User {user_id} not found for notification")
    except Exception as e:
        logger.error(f"Failed to create notification: {e}")


@shared_task
def send_push_notification_task(notification_id):
    try:
        notification = Notification.objects.get(id=notification_id)
        logger.info(f'[FCM DEBUG] Starting push notification for Notification ID: {notification_id}, User ID: {notification.user.id}')
        
        if messaging is None:
            logger.warning('[FCM DEBUG] Firebase Admin SDK is not available; skipping push notification.')
            return

        tokens = list(
            FCMToken.objects.filter(user=notification.user, is_active=True).values_list('token', flat=True)
        )
        if not tokens:
            logger.info(f'[FCM DEBUG] No active FCM tokens registered for user ID {notification.user.id}')
            return

        logger.info(f'[FCM DEBUG] Sending notification to {len(tokens)} token(s) for user {notification.user.id}: {tokens}')
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=notification.title,
                body=notification.body,
            ),
            data={str(k): str(v) for k, v in (notification.data or {}).items()} if notification.data else {'type': 'notification'},
            tokens=tokens,
        )
        response = messaging.send_each_for_multicast(message)
        logger.info(f'[FCM DEBUG] Multicast sent. Success count: {response.success_count}, Failure count: {response.failure_count}')
        
        if response.failure_count:
            for idx, resp in enumerate(response.responses):
                if not resp.success:
                    logger.warning(f'[FCM DEBUG] Token failure [{tokens[idx]}]: {resp.exception}')
                    
        notification.is_read = False
        notification.save(update_fields=['is_read'])
    except Exception as exc:
        logger.error(f'[FCM DEBUG] Push notification failed with exception: {exc}', exc_info=True)



@shared_task
def send_websocket_notification_task(notification_id):
    try:
        notification = Notification.objects.get(id=notification_id)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'user_{notification.user.id}',
            {
                'type': 'notification_message',
                'notification': {
                    'id': notification.id,
                    'notif_type': notification.notif_type,
                    'title': notification.title,
                    'body': notification.body,
                    'data': notification.data or {},
                    'created_at': notification.created_at.isoformat(),
                },
            },
        )
        notification.is_read = False
        notification.save(update_fields=['is_read'])
    except Exception as exc:
        logger.error(f'WebSocket notification failed: {exc}')


@shared_task
def notify_all_online_providers_task(booking_id, service_name, service_city, service_address, total_amount, distance_km, service_latitude=None, service_longitude=None):
    try:
        # Notify only approved online providers who offer this service and are within their service radius
        online_providers = ProviderProfile.objects.filter(
            is_online=True,
            status=ProviderProfile.STATUS_APPROVED,
        ).select_related('user')

        notifications = []
        for p in online_providers:
            # find if provider offers this service
            offers = ProviderService.objects.filter(provider=p, is_active=True).select_related('service')
            matches_service = False
            for s in offers:
                if service_name and s.service.name.lower() == service_name.lower():
                    matches_service = True
                    break
            if not matches_service:
                continue

            # if provider has no service location or booking has no coords, fallback to client distance_km
            if service_latitude is None or service_longitude is None or not (p.service_latitude and p.service_longitude and p.service_radius_km):
                # use provided distance_km if given
                try:
                    dist = float(distance_km or 0)
                except Exception:
                    dist = 0.0
            else:
                dist = haversine_distance_km(p.service_latitude, p.service_longitude, service_latitude, service_longitude)

            if dist > float(p.service_radius_km):
                continue

            location = service_city or (service_address[:40] if service_address else 'Unknown')
            notifications.append(Notification(
                user=p.user,
                notif_type=Notification.TYPE_BOOKING_NEW,
                title="New Job Request!",
                body=f"New {service_name or 'wash'} job at {location}.",
                data={
                    "booking_id": booking_id,
                    "earnings": str(total_amount),
                    "distance": str(distance_km),
                },
            ))

        if notifications:
            Notification.objects.bulk_create(notifications, ignore_conflicts=True)
            logger.info(f"Notified {len(notifications)} online providers about booking #{booking_id}")
    except Exception as e:
        logger.error(f"Failed to notify providers for booking #{booking_id}: {e}")


@shared_task
def bulk_create_notifications_task(user_ids, notif_type, title, body, data=None):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        users = User.objects.filter(id__in=user_ids)
        notifications = [
            Notification(user=u, notif_type=notif_type, title=title, body=body, data=data or {})
            for u in users
        ]
        Notification.objects.bulk_create(notifications, ignore_conflicts=True)
        logger.info(f"Bulk notification sent to {len(notifications)} users")
    except Exception as e:
        logger.error(f"Failed to bulk create notifications: {e}")
