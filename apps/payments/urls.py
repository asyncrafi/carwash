from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('create-payment-intent/', views.CreatePaymentIntentView.as_view(), name='create-payment-intent'),
    path('connect/onboard/', views.ConnectOnboardingView.as_view(), name='connect-onboard'),
    path('release-payout/', views.ReleasePayoutView.as_view(), name='release-payout'),
    path('stripe/webhook/', views.StripeWebhookView.as_view(), name='stripe-webhook'),
    path('earnings/', views.ProviderEarningsView.as_view(), name='earnings'),
]
