from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    ROLE_CUSTOMER = 'customer'
    ROLE_PROVIDER = 'provider'
    ROLE_ADMIN = 'admin'
    ROLE_CHOICES = [
        (ROLE_CUSTOMER, 'Customer'),
        (ROLE_PROVIDER, 'Provider'),
        (ROLE_ADMIN, 'Admin'),
    ]
    
    PROVIDER_GOOGLE = 'google'
    PROVIDER_FACEBOOK = 'facebook'
    PROVIDER_APPLE = 'apple'
    PROVIDER_CHOICES = [
        (PROVIDER_GOOGLE, 'Google'),
        (PROVIDER_FACEBOOK, 'Facebook'),
        (PROVIDER_APPLE, 'Apple'),
    ]
    
    full_name = models.CharField(max_length=255, blank=True, null=True)
    first_name = None
    last_name = None
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    language = models.CharField(max_length=10, default='en')
    social_auth_provider = models.CharField(
        max_length=20, 
        choices=PROVIDER_CHOICES,
        null=True, 
        blank=True,
        verbose_name="Social Auth Provider"
    )
    social_auth_id = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name="Social Auth ID"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.full_name or self.email} ({self.role})"


class OTPVerification(models.Model):
    PURPOSE_VERIFICATION = 'verification'
    PURPOSE_PASSWORD_RESET = 'password_reset'
    PURPOSE_EMAIL_CHANGE = 'email_change'
    PURPOSE_CHOICES = [
        (PURPOSE_VERIFICATION, 'Verification'),
        (PURPOSE_PASSWORD_RESET, 'Password Reset'),
        (PURPOSE_EMAIL_CHANGE, 'Email Change'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='otps'
    )
    code = models.CharField(max_length=6)
    purpose = models.CharField(
        max_length=20, choices=PURPOSE_CHOICES, default=PURPOSE_VERIFICATION
    )
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return not self.is_used and self.expires_at >= timezone.now()

    def __str__(self):
        return f"OTP for {self.user.email} ({self.purpose})"
