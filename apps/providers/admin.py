from django.contrib import admin
from .models import ProviderProfile, ProviderDocument, BankDetail, ProviderAvailability


class ProviderDocumentInline(admin.TabularInline):
    model = ProviderDocument
    extra = 0


class ProviderAvailabilityInline(admin.TabularInline):
    model = ProviderAvailability
    extra = 0


@admin.register(ProviderProfile)
class ProviderProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'is_online', 'total_washes', 'average_rating']
    list_filter = ['status', 'is_online']
    search_fields = ['user__phone', 'user__email', 'user__first_name', 'user__last_name']
    inlines = [ProviderDocumentInline, ProviderAvailabilityInline]


@admin.register(ProviderDocument)
class ProviderDocumentAdmin(admin.ModelAdmin):
    list_display = ['provider', 'doc_type', 'status', 'uploaded_at']
    list_filter = ['doc_type', 'status']


@admin.register(BankDetail)
class BankDetailAdmin(admin.ModelAdmin):
    list_display = ['provider', 'bank_name', 'bankholder_name']
