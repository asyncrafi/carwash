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
            'id', 'full_name', 'email', 'phone',
            'role', 'is_active', 'is_verified', 'avatar', 'date_joined',
        ]
        read_only_fields = fields


from rest_framework import serializers
from apps.services.models import VehicleType, EngineType, Service, DirtLevel


class VehicleTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleType
        fields = ['id', 'name', 'extra_price', 'is_active']


class EngineTypeSerializer(serializers.ModelSerializer):
    engine_type_display = serializers.CharField(
        source='get_engine_type_display', read_only=True
    )

    class Meta:
        model = EngineType
        fields = ['id', 'engine_type', 'engine_type_display', 'discount_percent', 'description']


class ServiceSerializer(serializers.ModelSerializer):
    vehicle_type_name = serializers.CharField(source='vehicle_type.name', read_only=True)
    engine_type_name = serializers.CharField(
        source='engine_type.get_engine_type_display', read_only=True
    )

    class Meta:
        model = Service
        fields = [
            'id', 'name', 'description', 'image',
            'base_price', 'is_active', 'order',
            'vehicle_type', 'vehicle_type_name',
            'engine_type', 'engine_type_name',
        ]


class DirtLevelSerializer(serializers.ModelSerializer):
    level_display = serializers.CharField(source='get_level_display', read_only=True)

    class Meta:
        model = DirtLevel
        fields = ['id', 'level', 'level_display', 'description', 'extra_price', 'image']