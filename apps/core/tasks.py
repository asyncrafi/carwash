import logging

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


@shared_task
def send_email_task(subject, email_to, template_name, context=None, email_from=None):
    try:
        context = context or {}
        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=email_from or settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email_to] if isinstance(email_to, str) else email_to,
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Email sent to {email_to}: {subject}")
    except Exception as e:
        logger.error(f"Failed to send email to {email_to}: {e}")
