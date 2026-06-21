from rest_framework import serializers
from .models import Booking, BookingPhoto
from apps.services.serializers import ServiceSerializer, DirtLevelSerializer
from apps.customers.serializers import VehicleSerializer, PaymentCardSerializer, CustomerBasicInfoSerializer
from apps.providers.serializers import ProviderBasicInfoSerializer
from apps.services.models import EngineType, VehicleType
from apps.customers.models import Vehicle as CustomerVehicle


class VehicleCreateSerializer(serializers.Serializer):
    engine_type = serializers.PrimaryKeyRelatedField(
        queryset=EngineType.objects.all(), required=False, allow_null=True
    )
    vehicle_type = serializers.PrimaryKeyRelatedField(
        queryset=VehicleType.objects.all(), required=False, allow_null=True
    )
    make = serializers.CharField(max_length=50, required=False, allow_blank=True)
    model = serializers.CharField(max_length=50, required=False, allow_blank=True)
    plate_number = serializers.CharField(max_length=20, required=False, allow_blank=True)


class BookingPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingPhoto
        fields = ['id', 'image', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class BookingCreateSerializer(serializers.ModelSerializer):
    photos = serializers.ListField(
        child=serializers.ImageField(), write_only=True, required=False
    )
    vehicle_data = VehicleCreateSerializer(write_only=True, required=False)

    class Meta:
        model = Booking
        fields = [
            'service', 'vehicle', 'dirt_level',
            'service_address', 'service_city',
            'service_latitude', 'service_longitude',
            'distance_km',
            'vehicle_data',
            'schedule_type', 'scheduled_at',
            'payment_card', 'photos',
        ]

    def validate(self, attrs):
        service = attrs.get('service')
        vehicle = attrs.get('vehicle')
        vehicle_data = attrs.get('vehicle_data')
        
        # If a saved vehicle is provided, validate compatibility
        if service and vehicle:
            if service.vehicle_type and service.vehicle_type != vehicle.vehicle_type:
                raise serializers.ValidationError(
                    {"service": f"Selected service '{service.name}' is only available for vehicle type '{service.vehicle_type.name}'."}
                )
            if service.engine_type and service.engine_type != vehicle.engine_type:
                raise serializers.ValidationError(
                    {"service": f"Selected service '{service.name}' is only available for engine type '{service.engine_type.get_engine_type_display()}'."}
                )

        # If inline vehicle data is provided (no saved vehicle), validate compatibility
        if service and not vehicle and vehicle_data:
            vt = vehicle_data.get('vehicle_type')
            et = vehicle_data.get('engine_type')
            if service.vehicle_type and vt and service.vehicle_type != vt:
                raise serializers.ValidationError(
                    {"service": f"Selected service '{service.name}' is only available for vehicle type '{service.vehicle_type.name}'."}
                )
            if service.engine_type and et and service.engine_type != et:
                raise serializers.ValidationError(
                    {"service": f"Selected service '{service.name}' is only available for engine type '{service.engine_type.get_engine_type_display()}'."}
                )
        return attrs

    def create(self, validated_data):
        photos_data = validated_data.pop('photos', [])
        # If client sent inline vehicle data instead of existing vehicle PK, create it
        vehicle_data = validated_data.pop('vehicle_data', None)
        if not validated_data.get('vehicle') and vehicle_data:
            customer = validated_data.get('customer')
            # create a Customer Vehicle linked to the customer
            created_vehicle = CustomerVehicle.objects.create(
                customer=customer,
                engine_type=vehicle_data.get('engine_type'),
                vehicle_type=vehicle_data.get('vehicle_type'),
                make=vehicle_data.get('make', ''),
                model=vehicle_data.get('model', ''),
                plate_number=vehicle_data.get('plate_number', ''),
            )
            validated_data['vehicle'] = created_vehicle

        booking = Booking.objects.create(**validated_data)
        for photo in photos_data:
            BookingPhoto.objects.create(booking=booking, image=photo)
        return booking


class BookingListSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    provider_name = serializers.SerializerMethodField()
    provider_avatar = serializers.SerializerMethodField()
    provider_rating = serializers.SerializerMethodField()
    provider_distance_km = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id', 'service_name', 'status', 'total_amount',
            'provider_name', 'provider_avatar', 'provider_rating', 'provider_distance_km',
            'schedule_type', 'scheduled_at', 'created_at',
        ]

    def get_provider_name(self, obj):
        return obj.provider.user.full_name if obj.provider else None

    def get_provider_avatar(self, obj):
        if obj.provider and obj.provider.user.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.provider.user.avatar.url)
        return None

    def get_provider_rating(self, obj):
        return float(obj.provider.average_rating) if obj.provider else None

    def get_provider_distance_km(self, obj):
        if obj.provider:
            provider_lat = obj.provider.current_latitude or obj.provider.service_latitude
            provider_lon = obj.provider.current_longitude or obj.provider.service_longitude
            if (provider_lat is not None and provider_lon is not None and 
                    obj.service_latitude is not None and obj.service_longitude is not None):
                from apps.core.utils import haversine_distance_km
                dist = haversine_distance_km(
                    provider_lat, provider_lon,
                    obj.service_latitude, obj.service_longitude
                )
                return round(dist, 2)
        return None


class BookingDetailSerializer(serializers.ModelSerializer):
    customer = CustomerBasicInfoSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)
    vehicle = VehicleSerializer(read_only=True)
    dirt_level = DirtLevelSerializer(read_only=True)
    provider = ProviderBasicInfoSerializer(read_only=True)
    photos = BookingPhotoSerializer(many=True, read_only=True)
    payment_card = PaymentCardSerializer(read_only=True)
    provider_distance_km = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id', 'status', 'customer', 'service', 'vehicle', 'dirt_level', 'provider',
            'service_address', 'service_city',
            'service_latitude', 'service_longitude',
            'distance_km', 'provider_distance_km', 'schedule_type', 'scheduled_at',
            'service_price', 'vehicle_price', 'dirt_price', 'distance_price',
            'engine_discount', 'platform_fee', 'tip_amount', 'total_amount',
            'payment_card', 'is_paid', 'photos',
            'created_at', 'accepted_at', 'started_at', 'completed_at',
        ]
        read_only_fields = fields

    def get_provider_distance_km(self, obj):
        provider_lat = None
        provider_lon = None
        if obj.provider:
            provider_lat = obj.provider.current_latitude or obj.provider.service_latitude
            provider_lon = obj.provider.current_longitude or obj.provider.service_longitude
        else:
            request = self.context.get('request')
            if request and request.user and hasattr(request.user, 'provider_profile'):
                provider_lat = request.user.provider_profile.current_latitude or request.user.provider_profile.service_latitude
                provider_lon = request.user.provider_profile.current_longitude or request.user.provider_profile.service_longitude

        if (provider_lat is not None and provider_lon is not None and 
                obj.service_latitude is not None and obj.service_longitude is not None):
            from apps.core.utils import haversine_distance_km
            dist = haversine_distance_km(
                provider_lat, provider_lon,
                obj.service_latitude, obj.service_longitude
            )
            return round(dist, 2)
        return None


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
        source='customer.user.full_name', read_only=True
    )
    customer_avatar = serializers.SerializerMethodField()
    photos = BookingPhotoSerializer(many=True, read_only=True)
    provider_distance_km = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id', 'service_name', 'vehicle_type', 'engine_type',
            'customer_name', 'customer_avatar', 'service_address', 'distance_km', 'provider_distance_km',
            'total_amount', 'status', 'schedule_type', 'scheduled_at', 'photos', 'created_at',
        ]

    def get_customer_avatar(self, obj):
        if obj.customer and obj.customer.user.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.customer.user.avatar.url)
            return obj.customer.user.avatar.url
        return None

    def get_provider_distance_km(self, obj):
        request = self.context.get('request')
        if request and request.user and hasattr(request.user, 'provider_profile'):
            provider = request.user.provider_profile
            provider_lat = provider.current_latitude or provider.service_latitude
            provider_lon = provider.current_longitude or provider.service_longitude
            if (provider_lat is not None and provider_lon is not None and
                    obj.service_latitude is not None and obj.service_longitude is not None):
                from apps.core.utils import haversine_distance_km
                dist = haversine_distance_km(
                    provider_lat, provider_lon,
                    obj.service_latitude, obj.service_longitude
                )
                return round(dist, 2)
        return None
