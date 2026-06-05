from rest_framework import serializers
from apps.accounts.models import User
from apps.services.models import Service, PlatformConfig
from apps.providers.models import ProviderProfile
from apps.providers.serializers import ProviderProfileSerializer
from apps.providers.serializers import ProviderDocumentSerializer
from apps.bookings.serializers import BookingListSerializer, BookingDetailSerializer
from apps.payments.serializers import ProviderEarningSerializer
from apps.services.serializers import ServiceSerializer, PlatformConfigSerializer
from apps.notifications.serializers import NotificationSerializer


class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'first_name', 'last_name', 'email', 'phone',
            'role', 'is_active', 'is_verified', 'avatar', 'date_joined',
        ]
        read_only_fields = fields
