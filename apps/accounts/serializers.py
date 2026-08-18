import random
import datetime
import uuid
import requests

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
            'id', 'full_name',
            'email', 'role', 'password', 'password2',
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
        validated_data.setdefault('username', validated_data.get('email', str(uuid.uuid4())))
        user = User(**validated_data)
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
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class OTPRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    purpose = serializers.ChoiceField(
        choices=['verification', 'password_reset'], default='verification'
    )


class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
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
    email = serializers.EmailField()
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
            'id', 'full_name', 'phone',
            'email', 'role', 'avatar',
            'is_verified', 'language', 'created_at',
        ]
        read_only_fields = ['id', 'email', 'role', 'is_verified', 'created_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.avatar:
            request = self.context.get('request')
            if request:
                data['avatar'] = request.build_absolute_uri(instance.avatar.url)
        return data


class SocialAuthSerializer(serializers.Serializer):
    """
    Serializer for social authentication (Google, Facebook, Apple)
    """
    provider = serializers.ChoiceField(
        choices=['google', 'facebook', 'apple'],
        help_text="Social auth provider: google, facebook, or apple"
    )
    access_token = serializers.CharField(
        max_length=5000,
        write_only=True,
        help_text="Access token from social provider"
    )
    role = serializers.ChoiceField(
        choices=['customer', 'provider'],
        default='customer',
        help_text="User role: customer or provider"
    )

    def validate(self, data):
        provider = data.get('provider')
        access_token = data.get('access_token')

        if provider == 'google':
            user_info = self._verify_google_token(access_token)
        elif provider == 'facebook':
            user_info = self._verify_facebook_token(access_token)
        elif provider == 'apple':
            user_info = self._verify_apple_token(access_token)
        else:
            raise serializers.ValidationError("Invalid provider")

        if not user_info:
            raise serializers.ValidationError("Invalid or expired token")

        data['user_info'] = user_info
        return data

    def _verify_google_token(self, token):
        """Verify Google access token and get user info"""
        try:
            response = requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {token}'}
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            raise serializers.ValidationError(f"Google token verification failed: {str(e)}")

    def _verify_facebook_token(self, token):
        """Verify Facebook access token and get user info"""
        try:
            response = requests.get(
                'https://graph.facebook.com/me',
                params={
                    'access_token': token,
                    'fields': 'id,name,email,picture'
                }
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            raise serializers.ValidationError(f"Facebook token verification failed: {str(e)}")

    def _verify_apple_token(self, token):
        """Verify Apple token and get user info"""
        try:
            # Apple token validation is more complex and requires server-to-server verification
            # This is a simplified version - you may need to implement full JWT verification
            import jwt
            from jwt import PyJWTError

            try:
                # Decode without verification first to get header
                unverified = jwt.decode(token, options={"verify_signature": False})
                # In production, you should verify the signature against Apple's public keys
                return unverified
            except PyJWTError as e:
                raise serializers.ValidationError(f"Apple token verification failed: {str(e)}")
        except Exception as e:
            raise serializers.ValidationError(f"Apple token verification failed: {str(e)}")

    def create_or_login_user(self):
        """Create or login user based on social auth data"""
        user_info = self.validated_data.get('user_info')
        provider = self.validated_data.get('provider')
        role = self.validated_data.get('role')

        # Extract user info based on provider
        if provider == 'google':
            email = user_info.get('email')
            full_name = user_info.get('name')
            social_id = user_info.get('id')
        elif provider == 'facebook':
            email = user_info.get('email')
            full_name = user_info.get('name')
            social_id = user_info.get('id')
        elif provider == 'apple':
            email = user_info.get('email')
            full_name = user_info.get('name', 'Apple User')
            social_id = user_info.get('sub')
        else:
            raise serializers.ValidationError("Invalid provider")

        if not email:
            raise serializers.ValidationError("Email not provided by social provider")

        # Get or create user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'full_name': full_name,
                'role': role,
                'social_auth_provider': provider,
                'social_auth_id': social_id,
                'is_verified': True,  # Mark as verified since they're using social auth
                'username': email,
            }
        )

        # Update user if it already exists and has no social auth info
        if not created and not user.social_auth_provider:
            user.social_auth_provider = provider
            user.social_auth_id = social_id
            if not user.full_name:
                user.full_name = full_name
            if not user.is_verified:
                user.is_verified = True
            user.save()

        # Create customer/provider profile if needed
        if created:
            if user.role == User.ROLE_CUSTOMER:
                CustomerProfile.objects.get_or_create(user=user)
            elif user.role == User.ROLE_PROVIDER:
                ProviderProfile.objects.get_or_create(user=user)

        return user

