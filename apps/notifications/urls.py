from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='list'),
    path('register-token/', views.FCMTokenRegisterView.as_view(), name='fcm-token'),
    path('preferences/', views.NotificationPreferencesView.as_view(), name='preferences'),
    path('read-all/', views.NotificationMarkAllReadView.as_view(), name='read-all'),
    path('<int:pk>/read/', views.NotificationMarkReadView.as_view(), name='read'),
]
