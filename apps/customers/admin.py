from django.contrib import admin
from .models import CustomerProfile, SavedAddress, PaymentCard, Vehicle


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at']
    search_fields = ['user__phone', 'user__email', 'user__first_name', 'user__last_name']


@admin.register(SavedAddress)
class SavedAddressAdmin(admin.ModelAdmin):
    list_display = ['customer', 'label', 'city', 'country', 'is_default']
    list_filter = ['label', 'is_default']


@admin.register(PaymentCard)
class PaymentCardAdmin(admin.ModelAdmin):
    list_display = ['customer', 'card_type', 'last_four', 'is_default']
    list_filter = ['card_type', 'is_default']


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['customer', 'make', 'model', 'plate_number', 'is_default']
