from django.urls import path
from . import views

app_name = 'providers'

urlpatterns = [
    path('profile/', views.ProviderProfileView.as_view(), name='profile'),
    path('online-status/', views.ProviderOnlineStatusView.as_view(), name='online-status'),
    path('location/', views.ProviderLocationUpdateView.as_view(), name='location'),
    path('documents/', views.ProviderDocumentUploadView.as_view(), name='documents'),
    path('bank/', views.BankDetailView.as_view(), name='bank'),
    path('availability/', views.ProviderAvailabilityView.as_view(), name='availability'),
]
