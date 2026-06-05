import logging

from celery import shared_task
from django.db import transaction

from .models import Notification
from apps.providers.models import ProviderProfile

logger = logging.getLogger(__name__)


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
def notify_all_online_providers_task(booking_id, service_name, service_city, service_address, total_amount, distance_km):
    try:
        online_providers = ProviderProfile.objects.filter(
            is_online=True,
            status=ProviderProfile.STATUS_APPROVED,
        ).select_related('user')

        location = service_city or service_address[:40] if service_address else 'Unknown'
        notifications = []
        for p in online_providers:
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
