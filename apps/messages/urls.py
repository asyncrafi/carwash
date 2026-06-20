from django.urls import path
from . import views

app_name = 'messages'

urlpatterns = [
    path('', views.ChatMessageListCreateView.as_view(), name='messages'),
    path('booking/<int:booking_pk>/', views.ChatMessageListCreateView.as_view(), name='messages-booking'),
    path('user/<int:other_user_id>/', views.ChatMessageListCreateView.as_view(), name='messages-user'),
    path('calls/', views.CallLogCreateView.as_view(), name='calls'),
]
