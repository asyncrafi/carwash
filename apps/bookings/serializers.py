from rest_framework import serializers
from .models import Booking, BookingPhoto
from apps.services.serializers import ServiceSerializer, DirtLevelSerializer
from apps.customers.serializers import VehicleSerializer, PaymentCardSerializer
from apps.providers.serializers import ProviderBasicInfoSerializer


class BookingPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingPhoto
        fields = ['id', 'image', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class BookingCreateSerializer(serializers.ModelSerializer):
    photos = serializers.ListField(
        child=serializers.ImageField(), write_only=True, required=False
    )

    class Meta:
        model = Booking
        fields = [
            'service', 'vehicle', 'dirt_level',
            'service_address', 'service_city',
            'service_latitude', 'service_longitude',
            'schedule_type', 'scheduled_at',
            'payment_card', 'photos',
        ]

    def create(self, validated_data):
        photos_data = validated_data.pop('photos', [])
        booking = Booking.objects.create(**validated_data)
        for photo in photos_data:
            BookingPhoto.objects.create(booking=booking, image=photo)
        return booking


class BookingListSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    provider_name = serializers.SerializerMethodField()
    provider_avatar = serializers.SerializerMethodField()
    provider_rating = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id', 'service_name', 'status', 'total_amount',
            'provider_name', 'provider_avatar', 'provider_rating',
            'schedule_type', 'scheduled_at', 'created_at',
        ]

    def get_provider_name(self, obj):
        return obj.provider.user.get_full_name() if obj.provider else None

    def get_provider_avatar(self, obj):
        if obj.provider and obj.provider.user.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.provider.user.avatar.url)
        return None

    def get_provider_rating(self, obj):
        return float(obj.provider.average_rating) if obj.provider else None


class BookingDetailSerializer(serializers.ModelSerializer):
    service = ServiceSerializer(read_only=True)
    vehicle = VehicleSerializer(read_only=True)
    dirt_level = DirtLevelSerializer(read_only=True)
    provider = ProviderBasicInfoSerializer(read_only=True)
    photos = BookingPhotoSerializer(many=True, read_only=True)
    payment_card = PaymentCardSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'status', 'service', 'vehicle', 'dirt_level', 'provider',
            'service_address', 'service_city',
            'service_latitude', 'service_longitude',
            'distance_km', 'schedule_type', 'scheduled_at',
            'service_price', 'vehicle_price', 'dirt_price', 'distance_price',
            'engine_discount', 'platform_fee', 'tip_amount', 'total_amount',
            'payment_card', 'is_paid', 'photos',
            'created_at', 'accepted_at', 'started_at', 'completed_at',
        ]
        read_only_fields = fields


class BookingStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Booking.STATUS_CHOICES)
    cancel_reason = serializers.CharField(required=False, allow_blank=True)


class JobListSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    vehicle_type = serializers.CharField(
        source='vehicle.vehicle_type.name', read_only=True
    )
    engine_type = serializers.CharField(
        source='vehicle.engine_type.engine_type', read_only=True
    )
    customer_name = serializers.CharField(
        source='customer.user.get_full_name', read_only=True
    )
    photos = BookingPhotoSerializer(many=True, read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'service_name', 'vehicle_type', 'engine_type',
            'customer_name', 'service_address', 'distance_km',
            'total_amount', 'status', 'scheduled_at', 'photos', 'created_at',
        ]
