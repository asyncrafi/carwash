from django.contrib import admin
from .models import Booking, BookingPhoto


class BookingPhotoInline(admin.TabularInline):
    model = BookingPhoto
    extra = 0


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'customer', 'provider', 'service', 'status',
        'total_amount', 'is_paid', 'created_at',
    ]
    list_filter = ['status', 'is_paid', 'schedule_type']
    search_fields = [
        'customer__user__phone', 'customer__user__first_name',
        'provider__user__phone',
    ]
    inlines = [BookingPhotoInline]
    readonly_fields = [
        'service_price', 'vehicle_price', 'dirt_price', 'distance_price',
        'engine_discount', 'platform_fee', 'total_amount',
    ]


@admin.register(BookingPhoto)
class BookingPhotoAdmin(admin.ModelAdmin):
    list_display = ['booking', 'uploaded_at']
