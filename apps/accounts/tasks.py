import logging

from celery import shared_task

from apps.core.tasks import send_email_task

logger = logging.getLogger(__name__)


@shared_task
def send_welcome_email_task(user_id, email, full_name):
    send_email_task.delay(
        subject="Welcome to CarWash!",
        email_to=email,
        template_name="emails/welcome.html",
        context={"name": full_name, "user_id": user_id},
    )


@shared_task
def send_otp_email_task(email, code, full_name):
    send_email_task.delay(
        subject="Your CarWash Verification Code",
        email_to=email,
        template_name="emails/otp.html",
        context={"name": full_name, "code": code},
    )


@shared_task
def send_password_reset_email_task(email, code, full_name):
    send_email_task.delay(
        subject="Reset Your CarWash Password",
        email_to=email,
        template_name="emails/password_reset.html",
        context={"name": full_name, "code": code},
    )


@shared_task
def send_provider_approved_email_task(email, full_name):
    send_email_task.delay(
        subject="Your Provider Account is Approved!",
        email_to=email,
        template_name="emails/provider_approved.html",
        context={"name": full_name},
    )
