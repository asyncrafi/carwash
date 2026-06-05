from django.db import models
from django.conf import settings


class Notification(models.Model):
    TYPE_BOOKING_NEW = 'booking_new'
    TYPE_BOOKING_ACCEPTED = 'booking_accepted'
    TYPE_BOOKING_EN_ROUTE = 'booking_en_route'
    TYPE_BOOKING_DONE = 'booking_done'
    TYPE_PAYMENT = 'payment'
    TYPE_DOCUMENT = 'document'
    TYPE_GENERAL = 'general'
    TYPE_CHOICES = [
        (TYPE_BOOKING_NEW, 'New Booking'),
        (TYPE_BOOKING_ACCEPTED, 'Booking Accepted'),
        (TYPE_BOOKING_EN_ROUTE, 'Provider En Route'),
        (TYPE_BOOKING_DONE, 'Booking Completed'),
        (TYPE_PAYMENT, 'Payment'),
        (TYPE_DOCUMENT, 'Document'),
        (TYPE_GENERAL, 'General'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    notif_type = models.CharField(
        max_length=25, choices=TYPE_CHOICES, default=TYPE_GENERAL
    )
    title = models.CharField(max_length=200)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.notif_type}] {self.title} → {self.user.phone}"
