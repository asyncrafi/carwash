from django.contrib import admin
from .models import Service, VehicleType, EngineType, DirtLevel, PlatformConfig


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'base_price', 'is_active', 'order']
    list_editable = ['is_active', 'order']
    list_filter = ['is_active']


@admin.register(VehicleType)
class VehicleTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'extra_price', 'is_active']


@admin.register(EngineType)
class EngineTypeAdmin(admin.ModelAdmin):
    list_display = ['engine_type', 'discount_percent']


@admin.register(DirtLevel)
class DirtLevelAdmin(admin.ModelAdmin):
    list_display = ['level', 'extra_price']


@admin.register(PlatformConfig)
class PlatformConfigAdmin(admin.ModelAdmin):
    list_display = ['platform_fee_fixed', 'commission_percent', 'distance_price_per_km']
