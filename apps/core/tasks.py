import logging

import resend
from celery import shared_task
from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

resend.api_key = settings.RESEND_API_KEY


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_email_task(self, subject, email_to, template_name, context=None):
    context = context or {}
    html_content = render_to_string(template_name, context)

    try:
        resend.Emails.send({
            "from": settings.DEFAULT_FROM_EMAIL,
            "to": [email_to],
            "subject": subject,
            "html": html_content,
        })
        logger.info(f"Email sent to {email_to} — subject: {subject}")
    except Exception as exc:
        logger.error(f"Resend send failed for {email_to}: {exc}")
        raise self.retry(exc=exc)