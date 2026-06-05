from django.db import models

from apps.bookings.models import Booking
from apps.providers.models import ProviderProfile


class Payment(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_SUCCESS = 'success'
    STATUS_FAILED = 'failed'
    STATUS_REFUNDED = 'refunded'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_SUCCESS, 'Success'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_REFUNDED, 'Refunded'),
    ]

    booking = models.OneToOneField(
        Booking, on_delete=models.CASCADE, related_name='payment'
    )
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(max_length=3, default='EUR')
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    gateway = models.CharField(max_length=50, default='stripe')
    transaction_id = models.CharField(max_length=255, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment #{self.id} - {self.amount} EUR [{self.status}]"


class ProviderEarning(models.Model):
    provider = models.ForeignKey(
        ProviderProfile, on_delete=models.CASCADE, related_name='earnings'
    )
    booking = models.OneToOneField(
        Booking, on_delete=models.CASCADE, related_name='earning'
    )
    gross_amount = models.DecimalField(max_digits=8, decimal_places=2)
    platform_fee = models.DecimalField(max_digits=8, decimal_places=2)
    net_amount = models.DecimalField(max_digits=8, decimal_places=2)
    is_paid_out = models.BooleanField(default=False)
    paid_out_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"Earning {self.provider.user.get_full_name()} - "
            f"€{self.net_amount}"
        )
