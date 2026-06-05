from rest_framework import serializers
from .models import Payment, ProviderEarning


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id', 'amount', 'currency', 'status',
            'gateway', 'transaction_id', 'paid_at', 'created_at',
        ]
        read_only_fields = fields


class ProviderEarningSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(
        source='booking.service.name', read_only=True
    )
    booked_at = serializers.DateTimeField(
        source='booking.created_at', read_only=True
    )

    class Meta:
        model = ProviderEarning
        fields = [
            'id', 'service_name', 'booked_at', 'gross_amount',
            'platform_fee', 'net_amount', 'is_paid_out',
            'paid_out_at', 'created_at',
        ]
        read_only_fields = fields
