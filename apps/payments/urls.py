from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('earnings/', views.ProviderEarningsView.as_view(), name='earnings'),
]
