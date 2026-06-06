import random
import datetime

from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.mixins import BaseResponseMixin
from apps.accounts.tasks import send_password_reset_email_task
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
    ChangePasswordSerializer,
    CreateNewPasswordSerializer,
    UserSerializer,
)
from .models import OTPVerification

User = get_user_model()


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class RegisterView(BaseResponseMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone = request.data.get('phone')

        if phone:
            try:
                user = User.objects.get(phone=phone)
                if user.is_verified:
                    return self.success_response(
                        data={
                            'phone': phone,
                            'is_sent': False,
                        },
                        message='User with this phone already exists and is verified.',
                        status_code=status.HTTP_200_OK,
                    )
                else:
                    serializer = RegisterSerializer()
                    code = serializer.send_verification_otp(user)
                    return self.success_response(
                        data={
                            'phone': phone,
                            'is_sent': True,
                            'otp_code': code,
                        },
                        message='User not verified. New OTP sent.',
                        status_code=status.HTTP_200_OK,
                    )
            except User.DoesNotExist:
                pass

        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        last_otp = user.otps.filter(
            purpose=OTPVerification.PURPOSE_VERIFICATION, is_used=False,
        ).order_by('-created_at').first()
        code = last_otp.code if last_otp else None

        return self.created_response(
            data={
                'user': UserSerializer(user).data,
                'otp_code': code,
                'is_sent': True,
            },
            message='Registration successful. Please verify your phone with the OTP code.',
        )


class LoginView(BaseResponseMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=serializer.validated_data['phone'],
            password=serializer.validated_data['password'],
        )
        if not user:
            return self.error_response(
                message="Invalid credentials.",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        tokens = get_tokens_for_user(user)
        data = {
            'user': UserSerializer(user).data,
            'tokens': tokens,
        }
        return self.success_response(data=data, message="Login successful.")


class LogoutView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return self.bad_request_response(message="Refresh token is required.")
        token = RefreshToken(refresh_token)
        token.blacklist()
        return self.success_response(message="Logged out successfully.")


class OTPRequestView(BaseResponseMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone']
        purpose = serializer.validated_data.get('purpose', OTPVerification.PURPOSE_VERIFICATION)
        user = get_object_or_404(User, phone=phone)
        code = str(random.randint(100000, 999999))
        OTPVerification.objects.create(
            user=user,
            code=code,
            purpose=purpose,
            expires_at=timezone.now() + datetime.timedelta(minutes=10),
        )
        return self.success_response(data={'otp_code': code}, message="OTP sent successfully.")


class OTPVerifyView(BaseResponseMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone']
        code = serializer.validated_data['code']
        user = get_object_or_404(User, phone=phone)
        otp = OTPVerification.objects.filter(
            user=user, code=code, purpose=OTPVerification.PURPOSE_VERIFICATION,
            is_used=False, expires_at__gte=timezone.now()
        ).order_by('-created_at').first()
        if not otp:
            return self.error_response(message="Invalid or expired OTP.")
        otp.is_used = True
        otp.save()
        user.is_verified = True
        user.save()
        tokens = get_tokens_for_user(user)
        data = {'tokens': tokens}
        return self.success_response(data=data, message="Phone verified successfully.")


class ChangePasswordView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return self.error_response(message="Old password is incorrect.")
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return self.success_response(message="Password changed successfully.")


class CreateNewPasswordView(BaseResponseMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CreateNewPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone']
        code = serializer.validated_data['code']
        user = get_object_or_404(User, phone=phone)
        otp = OTPVerification.objects.filter(
            user=user, code=code, purpose=OTPVerification.PURPOSE_PASSWORD_RESET,
            is_used=False, expires_at__gte=timezone.now()
        ).order_by('-created_at').first()
        if not otp:
            return self.error_response(message="Invalid or expired OTP.")
        otp.is_used = True
        otp.save()
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        if user.email:
            send_password_reset_email_task.delay(
                email=user.email,
                code=code,
                first_name=user.first_name or user.phone,
            )
        return self.success_response(message="Password reset successful.")


class UserProfileView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = UserSerializer(request.user).data
        return self.success_response(data=data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.updated_response(data=serializer.data)


class LanguageUpdateView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        lang = request.data.get('language')
        if not lang:
            return self.bad_request_response(message="Language field is required.")
        request.user.language = lang
        request.user.save()
        return self.success_response(message="Language updated successfully.")
