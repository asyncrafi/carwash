from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('', views.BookingCreateView.as_view(), name='create'),
    path('list/', views.CustomerBookingListView.as_view(), name='list'),
    path('<int:pk>/', views.CustomerBookingDetailView.as_view(), name='detail'),
    path('<int:pk>/tip/', views.BookingAddTipView.as_view(), name='tip'),
    path('<int:pk>/rate/', views.BookingRateView.as_view(), name='rate'),
    path('jobs/', views.ProviderJobListView.as_view(), name='job-list'),
    path('jobs/<int:pk>/', views.ProviderJobDetailView.as_view(), name='job-detail'),
    path('jobs/<int:pk>/accept/', views.ProviderJobAcceptView.as_view(), name='job-accept'),
    path('jobs/<int:pk>/reject/', views.ProviderJobRejectView.as_view(), name='job-reject'),
    path('jobs/<int:pk>/status/', views.ProviderJobStatusUpdateView.as_view(), name='job-status'),
]
