import logging

from celery import shared_task
from django.db import transaction

from .models import Notification
from apps.providers.models import ProviderProfile, ProviderService
from apps.core.utils import haversine_distance_km

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
