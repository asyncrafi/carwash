from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.accounts.models import User
from apps.customers.models import CustomerProfile, PaymentCard, Vehicle
from apps.providers.models import ProviderProfile
from apps.services.models import Service, DirtLevel


class Booking(models.Model):
    STATUS_REQUESTED = 'requested'
    STATUS_ACCEPTED = 'accepted'
    STATUS_EN_ROUTE = 'en_route'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_REQUESTED, 'Requested'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_EN_ROUTE, 'En Route'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]
    SCHEDULE_NOW = 'now'
    SCHEDULE_LATER = 'scheduled'
    SCHEDULE_CHOICES = [
        (SCHEDULE_NOW, 'Now'),
        (SCHEDULE_LATER, 'Scheduled'),
    ]

    customer = models.ForeignKey(
        CustomerProfile, on_delete=models.CASCADE, related_name='bookings'
    )
    provider = models.ForeignKey(
        ProviderProfile, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='jobs'
    )
    service = models.ForeignKey(
        Service, on_delete=models.SET_NULL, null=True
    )
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.SET_NULL, null=True
    )
    dirt_level = models.ForeignKey(
        DirtLevel, on_delete=models.SET_NULL, null=True
    )
    service_address = models.TextField()
    service_city = models.CharField(max_length=100, blank=True)
    service_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    service_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    distance_km = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    schedule_type = models.CharField(
        max_length=10, choices=SCHEDULE_CHOICES, default=SCHEDULE_NOW
    )
    scheduled_at = models.DateTimeField(null=True, blank=True)
    service_price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    vehicle_price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    dirt_price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    distance_price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    engine_discount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    platform_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    tip_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, default=STATUS_REQUESTED
    )
    payment_card = models.ForeignKey(
        PaymentCard, on_delete=models.SET_NULL, null=True, blank=True
    )
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancel_reason = models.TextField(blank=True)

    def __str__(self):
        return (
            f"Booking #{self.id} - "
            f"{self.customer.user.get_full_name()} [{self.status}]"
        )


class BookingPhoto(models.Model):
    booking = models.ForeignKey(
        Booking, on_delete=models.CASCADE, related_name='photos'
    )
    image = models.ImageField(upload_to='booking_photos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo for Booking #{self.booking.id}"
