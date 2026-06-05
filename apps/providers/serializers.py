from rest_framework import serializers
from .models import ProviderProfile, ProviderDocument, BankDetail, ProviderAvailability


class ProviderDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderDocument
        fields = [
            'id', 'doc_type', 'file', 'status',
            'admin_note', 'uploaded_at', 'reviewed_at',
        ]
        read_only_fields = ['id', 'status', 'admin_note', 'uploaded_at', 'reviewed_at']


class BankDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankDetail
        fields = [
            'id', 'account_number', 'routing_number', 'bank_name',
            'bankholder_name', 'bank_address', 'updated_at',
        ]
        read_only_fields = ['id', 'updated_at']


class ProviderAvailabilitySerializer(serializers.ModelSerializer):
    day_display = serializers.CharField(
        source='get_day_of_week_display', read_only=True
    )

    class Meta:
        model = ProviderAvailability
        fields = [
            'id', 'day_of_week', 'day_display',
            'start_time', 'end_time', 'is_active',
        ]
        read_only_fields = ['id', 'day_display']


class ProviderProfileSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    documents = ProviderDocumentSerializer(many=True, read_only=True)
    bank_detail = BankDetailSerializer(read_only=True)
    availability = ProviderAvailabilitySerializer(many=True, read_only=True)

    class Meta:
        model = ProviderProfile
        fields = [
            'id', 'user', 'status', 'is_online',
            'current_latitude', 'current_longitude', 'bio',
            'total_washes', 'average_rating',
            'documents', 'bank_detail', 'availability', 'created_at',
        ]
        read_only_fields = [
            'id', 'status', 'total_washes', 'average_rating', 'created_at',
        ]

    def get_user(self, obj):
        from apps.accounts.serializers import UserSerializer
        return UserSerializer(obj.user).data


class ProviderLocationSerializer(serializers.Serializer):
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)


class ProviderOnlineStatusSerializer(serializers.Serializer):
    is_online = serializers.BooleanField()


class ProviderBasicInfoSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    avatar = serializers.ImageField(source='user.avatar', read_only=True)
    phone = serializers.CharField(source='user.phone', read_only=True)

    class Meta:
        model = ProviderProfile
        fields = [
            'id', 'full_name', 'avatar', 'phone',
            'average_rating', 'total_washes', 'is_online',
        ]
