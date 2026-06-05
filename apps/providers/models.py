from django.db import models
from django.conf import settings


class ProviderProfile(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='provider_profile',
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    is_online = models.BooleanField(default=False)
    current_latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    current_longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    bio = models.TextField(blank=True)
    total_washes = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(
        max_digits=3, decimal_places=2, default=0.00
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Provider: {self.user.get_full_name()} [{self.status}]"


class ProviderDocument(models.Model):
    TYPE_ID_FRONT = 'id_front'
    TYPE_ID_BACK = 'id_back'
    TYPE_SIRET = 'siret'
    TYPE_PROOF_ADDRESS = 'proof_address'
    TYPE_LIABILITY_INS = 'liability_insurance'
    TYPE_URSSAF = 'urssaf'
    TYPE_CHOICES = [
        (TYPE_ID_FRONT, 'ID Card (Front)'),
        (TYPE_ID_BACK, 'ID Card (Back)'),
        (TYPE_SIRET, 'SIRET Certificate'),
        (TYPE_PROOF_ADDRESS, 'Proof of Address'),
        (TYPE_LIABILITY_INS, 'Liability Insurance'),
        (TYPE_URSSAF, 'URSSAF Vigilance'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    provider = models.ForeignKey(
        ProviderProfile, on_delete=models.CASCADE, related_name='documents'
    )
    doc_type = models.CharField(max_length=25, choices=TYPE_CHOICES)
    file = models.FileField(upload_to='provider_docs/')
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    admin_note = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('provider', 'doc_type')

    def __str__(self):
        return f"{self.provider.user.get_full_name()} - {self.doc_type}"


class BankDetail(models.Model):
    provider = models.OneToOneField(
        ProviderProfile, on_delete=models.CASCADE, related_name='bank_detail'
    )
    account_number = models.CharField(max_length=50)
    routing_number = models.CharField(max_length=50)
    bank_name = models.CharField(max_length=100)
    bankholder_name = models.CharField(max_length=100)
    bank_address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.bankholder_name} - {self.bank_name}"


class ProviderAvailability(models.Model):
    DAY_CHOICES = [
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'),
    ]

    provider = models.ForeignKey(
        ProviderProfile, on_delete=models.CASCADE, related_name='availability'
    )
    day_of_week = models.PositiveSmallIntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('provider', 'day_of_week')

    def __str__(self):
        return f"{self.provider.user.get_full_name()} - {self.get_day_of_week_display()}"
