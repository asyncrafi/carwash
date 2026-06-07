from django.contrib import admin
from .models import Service, VehicleType, EngineType, DirtLevel, PlatformConfig


class ServiceVehicleInline(admin.TabularInline):
    model = Service
    fk_name = 'vehicle_type'
    extra = 1
    fields = ['name', 'engine_type', 'base_price', 'is_active', 'order']
    ordering = ['order']


class ServiceEngineInline(admin.TabularInline):
    model = Service
    fk_name = 'engine_type'
    extra = 1
    fields = ['name', 'vehicle_type', 'base_price', 'is_active', 'order']
    ordering = ['order']


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'vehicle_type', 'engine_type', 'base_price', 'is_active', 'order']
    list_editable = ['base_price', 'is_active', 'order']
    list_filter = ['vehicle_type', 'engine_type', 'is_active']
    search_fields = ['name', 'description']


@admin.register(VehicleType)
class VehicleTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'extra_price', 'is_active']
    list_editable = ['extra_price', 'is_active']
    inlines = [ServiceVehicleInline]


@admin.register(EngineType)
class EngineTypeAdmin(admin.ModelAdmin):
    list_display = ['engine_type', 'discount_percent', 'description']
    list_editable = ['discount_percent']
    inlines = [ServiceEngineInline]


@admin.register(DirtLevel)
class DirtLevelAdmin(admin.ModelAdmin):
    list_display = ['level', 'description', 'extra_price']
    list_editable = ['extra_price']


@admin.register(PlatformConfig)
class PlatformConfigAdmin(admin.ModelAdmin):
    list_display = ['platform_fee_fixed', 'commission_percent', 'distance_price_per_km', 'updated_at']
