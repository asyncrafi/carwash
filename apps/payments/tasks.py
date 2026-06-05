import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def create_provider_earning_task(booking_id):
    from apps.payments.utils import create_provider_earning
    from apps.bookings.models import Booking

    try:
        booking = Booking.objects.get(id=booking_id)
        create_provider_earning(booking)
    except Booking.DoesNotExist:
        logger.warning(f"Booking #{booking_id} not found for earning creation")
    except Exception as e:
        logger.error(f"Failed to create earning for booking #{booking_id}: {e}")


@shared_task
def send_booking_completed_email_task(customer_email, customer_name, provider_name, booking_id):
    from apps.core.tasks import send_email_task

    send_email_task.delay(
        subject="Your Car Wash is Complete!",
        email_to=customer_email,
        template_name="emails/booking_completed.html",
        context={
            "name": customer_name,
            "provider_name": provider_name,
            "booking_id": booking_id,
        },
    )
