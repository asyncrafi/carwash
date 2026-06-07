from rest_framework import serializers
from .models import Service, VehicleType, EngineType, DirtLevel, PlatformConfig


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = [
            'id', 'vehicle_type', 'engine_type', 'name',
            'description', 'image', 'base_price', 'is_active', 'order',
        ]
        read_only_fields = ['id']


class VehicleTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleType
        fields = ['id', 'name', 'extra_price', 'is_active']
        read_only_fields = ['id']


class EngineTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EngineType
        fields = ['id', 'engine_type', 'discount_percent', 'description']
        read_only_fields = ['id']


class DirtLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = DirtLevel
        fields = ['id', 'level', 'description', 'extra_price', 'image']
        read_only_fields = ['id']


class PlatformConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlatformConfig
        fields = [
            'platform_fee_fixed', 'commission_percent',
            'distance_price_per_km', 'updated_at',
        ]
        read_only_fields = ['updated_at']
