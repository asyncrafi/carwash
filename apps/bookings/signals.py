import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Booking
from .tasks import (
    handle_booking_created,
    handle_booking_accepted,
    handle_booking_en_route,
    handle_booking_in_progress,
    handle_booking_completed,
    handle_booking_cancelled,
)

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Booking)
def cache_old_booking_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_status = Booking.objects.get(pk=instance.pk).status
        except Booking.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Booking)
def on_booking_status_change(sender, instance, created, **kwargs):
    old_status = getattr(instance, '_old_status', None)
    new_status = instance.status

    if created:
        handle_booking_created.delay(
            booking_id=instance.id,
            customer_user_id=instance.customer.user.id,
            service_name=instance.service.name if instance.service else None,
            service_city=instance.service_city,
            service_address=instance.service_address,
            total_amount=str(instance.total_amount),
            distance_km=str(instance.distance_km),
            service_latitude=getattr(instance, 'service_latitude', None),
            service_longitude=getattr(instance, 'service_longitude', None),
        )
        return

    if old_status == new_status:
        return

    logger.info(f"Booking #{instance.id} status: {old_status} → {new_status}")

    if new_status == Booking.STATUS_ACCEPTED:
        handle_booking_accepted.delay(
            booking_id=instance.id,
            customer_user_id=instance.customer.user.id,
            provider_name=instance.provider.user.full_name,
        )

    elif new_status == Booking.STATUS_EN_ROUTE:
        handle_booking_en_route.delay(
            booking_id=instance.id,
            customer_user_id=instance.customer.user.id,
            provider_name=instance.provider.user.full_name,
        )

    elif new_status == Booking.STATUS_IN_PROGRESS:
        handle_booking_in_progress.delay(
            booking_id=instance.id,
            customer_user_id=instance.customer.user.id,
        )

    elif new_status == Booking.STATUS_COMPLETED:
        provider_user_id = instance.provider.user.id if instance.provider else None
        handle_booking_completed.delay(
            booking_id=instance.id,
            customer_user_id=instance.customer.user.id,
            provider_user_id=provider_user_id,
            customer_email=instance.customer.user.email,
            customer_name=instance.customer.user.full_name,
            provider_name=instance.provider.user.full_name if instance.provider else '',
            total_amount=str(instance.total_amount),
        )

    elif new_status == Booking.STATUS_CANCELLED:
        provider_user_id = instance.provider.user.id if instance.provider else None
        handle_booking_cancelled.delay(
            booking_id=instance.id,
            customer_user_id=instance.customer.user.id,
            provider_user_id=provider_user_id,
        )
