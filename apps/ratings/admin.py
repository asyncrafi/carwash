from django.contrib import admin
from .models import Rating, Tip


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['booking', 'reviewer', 'reviewee', 'stars', 'created_at']
    list_filter = ['stars']


@admin.register(Tip)
class TipAdmin(admin.ModelAdmin):
    list_display = ['booking', 'amount', 'created_at']
