from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    path('profile/', views.CustomerProfileView.as_view(), name='profile'),
    path('addresses/', views.SavedAddressListCreateView.as_view(), name='addresses'),
    path('addresses/<int:pk>/', views.SavedAddressDetailView.as_view(), name='address-detail'),
    path('cards/', views.PaymentCardListCreateView.as_view(), name='cards'),
    path('cards/<int:pk>/', views.PaymentCardDetailView.as_view(), name='card-detail'),
    path('vehicles/', views.VehicleListCreateView.as_view(), name='vehicles'),
    path('vehicles/<int:pk>/', views.VehicleDetailView.as_view(), name='vehicle-detail'),
]
