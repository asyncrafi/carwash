from celery import shared_task
from datetime import timedelta
from django.utils import timezone

from apps.notifications.tasks import (
    create_notification_task,
    notify_all_online_providers_task,
)
from apps.payments.tasks import create_provider_earning_task
from apps.accounts.tasks import send_welcome_email_task
from .models import Booking


@shared_task
def handle_booking_created(booking_id, customer_user_id, service_name, service_city,
                           service_address, total_amount, distance_km, service_latitude=None, service_longitude=None):
    notify_all_online_providers_task.delay(
        booking_id=booking_id,
        service_name=service_name,
        service_city=service_city,
        service_address=service_address,
        total_amount=total_amount,
        distance_km=distance_km,
        service_latitude=service_latitude,
        service_longitude=service_longitude,
    )
    create_notification_task.delay(
        user_id=customer_user_id,
        notif_type="booking_new",
        title="Booking Requested",
        body="Your booking has been placed. Looking for a provider nearby.",
        data={"booking_id": booking_id},
    )


@shared_task
def handle_booking_accepted(booking_id, customer_user_id, provider_name):
    create_notification_task.delay(
        user_id=customer_user_id,
        notif_type="booking_accepted",
        title="Provider Accepted",
        body=f"{provider_name} accepted your booking.",
        data={"booking_id": booking_id},
    )


@shared_task
def handle_booking_en_route(booking_id, customer_user_id, provider_name):
    create_notification_task.delay(
        user_id=customer_user_id,
        notif_type="booking_en_route",
        title="Provider On The Way",
        body=f"{provider_name} is heading to your location.",
        data={"booking_id": booking_id},
    )


@shared_task
def handle_booking_in_progress(booking_id, customer_user_id):
    create_notification_task.delay(
        user_id=customer_user_id,
        notif_type="booking_en_route",
        title="Service Started",
        body="Your car wash has started.",
        data={"booking_id": booking_id},
    )


@shared_task
def handle_booking_completed(booking_id, customer_user_id, provider_user_id,
                              customer_email, customer_name, provider_name, total_amount):
    create_notification_task.delay(
        user_id=customer_user_id,
        notif_type="booking_done",
        title="Service Completed!",
        body="Your car wash is done. Don't forget to rate your provider.",
        data={"booking_id": booking_id},
    )
    create_notification_task.delay(
        user_id=provider_user_id,
        notif_type="payment",
        title="Job Completed",
        body=f"You earned €{total_amount} for the completed job.",
        data={"booking_id": booking_id},
    )
    create_provider_earning_task.delay(booking_id=booking_id)


@shared_task
def handle_booking_cancelled(booking_id, customer_user_id, provider_user_id=None):
    create_notification_task.delay(
        user_id=customer_user_id,
        notif_type="general",
        title="Booking Cancelled",
        body="Your booking has been cancelled.",
        data={"booking_id": booking_id},
    )
    if provider_user_id:
        create_notification_task.delay(
            user_id=provider_user_id,
            notif_type="general",
            title="Job Cancelled",
            body="A booking assigned to you was cancelled.",
            data={"booking_id": booking_id},
        )


@shared_task
def handle_user_registered(user_id, email, full_name):
    send_welcome_email_task.delay(
        user_id=user_id,
        email=email,
        full_name=full_name,
    )


@shared_task
def delete_expired_now_bookings():
    """
    Auto-delete (cancel) bookings with 'now' schedule type that haven't been 
    accepted by any provider within 5 minutes of creation.
    Notifies the customer when their booking expires.
    """
    five_minutes_ago = timezone.now() - timedelta(minutes=5)
    
    # Find all expired "now" bookings that are still in requested status
    expired_bookings = Booking.objects.filter(
        status=Booking.STATUS_REQUESTED,
        provider__isnull=True,
        schedule_type=Booking.SCHEDULE_NOW,
        created_at__lt=five_minutes_ago
    )
    
    for booking in expired_bookings:
        # Cancel the booking
        booking.status = Booking.STATUS_CANCELLED
        booking.cancelled_at = timezone.now()
        booking.cancel_reason = "No provider accepted within 5 minutes"
        booking.save()
        
        # Notify the customer that their booking expired
        create_notification_task.delay(
            user_id=booking.customer.user.id,
            notif_type="booking_cancelled",
            title="Booking Expired",
            body="No provider accepted your booking within 5 minutes. It has been cancelled.",
            data={"booking_id": booking.id},
        )
