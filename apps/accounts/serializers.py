import random
import datetime

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone

from apps.customers.models import CustomerProfile
from apps.providers.models import ProviderProfile
from .models import OTPVerification

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'id', 'first_name', 'last_name', 'phone',
            'country_code', 'email', 'role', 'password', 'password2',
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {'password': "Password fields didn't match."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        validated_data.setdefault('country_code', '+33')
        validated_data.setdefault('email', '')
        user = User(**validated_data)
        user.username = validated_data.get('phone')
        user.is_verified = False
        user.set_password(password)
        user.save()
        if user.role == User.ROLE_CUSTOMER:
            CustomerProfile.objects.create(user=user)
        elif user.role == User.ROLE_PROVIDER:
            ProviderProfile.objects.create(user=user)
        self.send_verification_otp(user)
        return user

    def send_verification_otp(self, user):
        code = str(random.randint(100000, 999999))
        OTPVerification.objects.create(
            user=user,
            code=code,
            purpose=OTPVerification.PURPOSE_VERIFICATION,
            expires_at=timezone.now() + datetime.timedelta(minutes=10),
        )
        return code


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True)


class OTPRequestSerializer(serializers.Serializer):
    phone = serializers.CharField()
    purpose = serializers.ChoiceField(
        choices=['verification', 'password_reset'], default='verification'
    )


class OTPVerifySerializer(serializers.Serializer):
    phone = serializers.CharField()
    code = serializers.CharField(max_length=6)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data


class CreateNewPasswordSerializer(serializers.Serializer):
    phone = serializers.CharField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'first_name', 'last_name', 'phone',
            'country_code', 'email', 'role', 'avatar',
            'is_verified', 'language', 'created_at',
        ]
        read_only_fields = ['id', 'role', 'is_verified', 'created_at']
