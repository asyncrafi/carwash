from django.db import models
from django.conf import settings

from apps.bookings.models import Booking


class ChatMessage(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, null=True, blank=True, related_name='messages')
    text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender} to {self.recipient} ({self.created_at})"


class CallLog(models.Model):
    caller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='calls_made')
    callee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='calls_received')
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Call {self.caller} -> {self.callee} at {self.created_at}"


class LocationHistory(models.Model):
    """
    Stores real-time location updates during a booking.
    Used for tracking provider's live location during ride.
    """
    USER_TYPE_PROVIDER = 'provider'
    USER_TYPE_CUSTOMER = 'customer'
    USER_TYPE_CHOICES = [
        (USER_TYPE_PROVIDER, 'Provider'),
        (USER_TYPE_CUSTOMER, 'Customer'),
    ]

    booking = models.ForeignKey(
        Booking, 
        on_delete=models.CASCADE, 
        related_name='location_history'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='location_history'
    )
    user_type = models.CharField(
        max_length=10, 
        choices=USER_TYPE_CHOICES, 
        default=USER_TYPE_PROVIDER
    )
    latitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6
    )
    longitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6
    )
    accuracy = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Location accuracy in meters"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"Location update for Booking #{self.booking.id} by {self.user.full_name}"
