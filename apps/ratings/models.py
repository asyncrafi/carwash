from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings

from apps.bookings.models import Booking


class Rating(models.Model):
    booking = models.OneToOneField(
        Booking, on_delete=models.CASCADE, related_name='rating'
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='given_ratings',
    )
    reviewee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_ratings',
    )
    stars = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rating {self.stars}★ for {self.reviewee.get_full_name()}"


class Tip(models.Model):
    booking = models.OneToOneField(
        Booking, on_delete=models.CASCADE, related_name='tip'
    )
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Tip €{self.amount} for Booking #{self.booking.id}"
