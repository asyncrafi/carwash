from django.db import models
from django.conf import settings

from apps.services.models import EngineType, VehicleType


class CustomerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='customer_profile',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Customer: {self.user.get_full_name()}"


class SavedAddress(models.Model):
    LABEL_HOME = 'home'
    LABEL_OFFICE = 'office'
    LABEL_OTHER = 'other'
    LABEL_CHOICES = [
        (LABEL_HOME, 'Home'),
        (LABEL_OFFICE, 'Office'),
        (LABEL_OTHER, 'Other'),
    ]

    customer = models.ForeignKey(
        CustomerProfile, on_delete=models.CASCADE, related_name='saved_addresses'
    )
    label = models.CharField(max_length=10, choices=LABEL_CHOICES, default=LABEL_HOME)
    address = models.TextField()
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.label} - {self.address}"


class PaymentCard(models.Model):
    CARD_VISA = 'visa'
    CARD_MASTERCARD = 'mastercard'
    CARD_OTHER = 'other'
    CARD_CHOICES = [
        (CARD_VISA, 'Visa'),
        (CARD_MASTERCARD, 'Mastercard'),
        (CARD_OTHER, 'Other'),
    ]

    customer = models.ForeignKey(
        CustomerProfile, on_delete=models.CASCADE, related_name='payment_cards'
    )
    card_type = models.CharField(max_length=15, choices=CARD_CHOICES)
    last_four = models.CharField(max_length=4)
    cardholder_name = models.CharField(max_length=100)
    expiry_month = models.PositiveSmallIntegerField()
    expiry_year = models.PositiveSmallIntegerField()
    is_default = models.BooleanField(default=False)
    payment_token = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.card_type} **** {self.last_four}"


class Vehicle(models.Model):
    customer = models.ForeignKey(
        CustomerProfile, on_delete=models.CASCADE, related_name='vehicles'
    )
    engine_type = models.ForeignKey(
        EngineType, on_delete=models.SET_NULL, null=True
    )
    vehicle_type = models.ForeignKey(
        VehicleType, on_delete=models.SET_NULL, null=True
    )
    make = models.CharField(max_length=50, blank=True)
    model = models.CharField(max_length=50, blank=True)
    plate_number = models.CharField(max_length=20, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.make} {self.model} ({self.engine_type})"
