from .tasks import create_notification_task, notify_all_online_providers_task


def notify_user(user, notif_type, title, body, data=None):
    create_notification_task.delay(
        user_id=user.id,
        notif_type=notif_type,
        title=title,
        body=body,
        data=data,
    )


def notify_all_online_providers(booking):
    notify_all_online_providers_task.delay(
        booking_id=booking.id,
        service_name=booking.service.name if booking.service else None,
        service_city=booking.service_city,
        service_address=booking.service_address,
        total_amount=str(booking.total_amount),
        distance_km=str(booking.distance_km),
    )
