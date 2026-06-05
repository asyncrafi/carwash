from django.contrib import admin
from .models import Payment, ProviderEarning


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'booking', 'amount', 'currency', 'status', 'gateway', 'paid_at']
    list_filter = ['status', 'gateway', 'currency']
    search_fields = ['booking__id', 'transaction_id']


@admin.register(ProviderEarning)
class ProviderEarningAdmin(admin.ModelAdmin):
    list_display = ['provider', 'booking', 'gross_amount', 'platform_fee', 'net_amount', 'is_paid_out']
    list_filter = ['is_paid_out']
