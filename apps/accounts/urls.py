from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('otp/request/', views.OTPRequestView.as_view(), name='otp-request'),
    path('otp/verify/', views.OTPVerifyView.as_view(), name='otp-verify'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('reset-password/', views.CreateNewPasswordView.as_view(), name='reset-password'),
    path('me/', views.UserProfileView.as_view(), name='me'),
    path('me/language/', views.LanguageUpdateView.as_view(), name='me-language'),
]
    