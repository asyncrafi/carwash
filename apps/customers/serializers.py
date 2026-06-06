from rest_framework import serializers
from .models import SavedAddress, PaymentCard, CustomerProfile, Vehicle
from apps.services.serializers import EngineTypeSerializer, VehicleTypeSerializer


class SavedAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedAddress
        fields = [
            'id', 'label', 'address', 'city', 'country',
            'latitude', 'longitude', 'is_default', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class PaymentCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentCard
        fields = [
            'id', 'card_type', 'last_four', 'cardholder_name',
            'expiry_month', 'expiry_year', 'is_default',
            'payment_token', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {'payment_token': {'write_only': True}}


class CustomerProfileSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    saved_addresses = SavedAddressSerializer(many=True, read_only=True)
    payment_cards = PaymentCardSerializer(many=True, read_only=True)

    class Meta:
        model = CustomerProfile
        fields = [
            'id', 'user', 'saved_addresses', 'payment_cards', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_user(self, obj):
        from apps.accounts.serializers import UserSerializer
        return UserSerializer(obj.user, context=self.context).data


class VehicleSerializer(serializers.ModelSerializer):
    engine_type_detail = EngineTypeSerializer(source='engine_type', read_only=True)
    vehicle_type_detail = VehicleTypeSerializer(source='vehicle_type', read_only=True)

    class Meta:
        model = Vehicle
        fields = [
            'id', 'engine_type', 'engine_type_detail',
            'vehicle_type', 'vehicle_type_detail',
            'make', 'model', 'plate_number', 'is_default', 'created_at',
        ]
        read_only_fields = [
            'id', 'created_at', 'engine_type_detail', 'vehicle_type_detail',
        ]
