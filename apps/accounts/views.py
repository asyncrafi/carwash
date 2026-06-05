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
from apps.accounts.tasks import send_welcome_email_task, send_otp_email_task, send_password_reset_email_task
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
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        if user.email:
            send_welcome_email_task.delay(
                user_id=user.id,
                email=user.email,
                first_name=user.first_name or user.phone,
            )
        tokens = get_tokens_for_user(user)
        data = {
            'user': UserSerializer(user).data,
            'tokens': tokens,
        }
        return self.created_response(data=data, message="User registered successfully.")


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
        user = get_object_or_404(User, phone=phone)
        code = str(random.randint(100000, 999999))
        OTPVerification.objects.create(
            user=user,
            code=code,
            expires_at=timezone.now() + datetime.timedelta(minutes=10),
        )
        if user.email:
            send_otp_email_task.delay(
                email=user.email,
                code=code,
                first_name=user.first_name or user.phone,
            )
        return self.success_response(message="OTP sent successfully.")


class OTPVerifyView(BaseResponseMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone']
        code = serializer.validated_data['code']
        user = get_object_or_404(User, phone=phone)
        otp = OTPVerification.objects.filter(
            user=user, code=code, is_used=False,
            expires_at__gte=timezone.now()
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
            user=user, code=code, is_used=False,
            expires_at__gte=timezone.now()
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
