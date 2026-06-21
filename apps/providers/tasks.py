from celery import shared_task
from django.utils import timezone
from apps.notifications.tasks import create_notification_task


@shared_task
def send_documents_verified_email_task(provider_user_id):
    """
    Send email notification when provider documents are verified.
    """
    from apps.accounts.models import User
    
    try:
        user = User.objects.get(id=provider_user_id)
        # Send email via your email service
        # For now, just create a notification
        create_notification_task.delay(
            user_id=provider_user_id,
            notif_type="document_verified",
            title="Documents Verified ✅",
            body="Your documents have been verified. You're all set to accept jobs!",
            data={},
        )
    except User.DoesNotExist:
        pass


@shared_task
def send_documents_rejected_email_task(provider_user_id, rejection_reason):
    """
    Send email notification when provider documents are rejected.
    """
    from apps.accounts.models import User
    
    try:
        user = User.objects.get(id=provider_user_id)
        # Send email via your email service
        # For now, just create a notification
        create_notification_task.delay(
            user_id=provider_user_id,
            notif_type="document_rejected",
            title="Documents Rejected ❌",
            body=f"Your documents were rejected. Reason: {rejection_reason}. Please resubmit corrected documents.",
            data={"rejection_reason": rejection_reason},
        )
    except User.DoesNotExist:
        pass
