from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='list'),
    path('read-all/', views.NotificationMarkAllReadView.as_view(), name='read-all'),
    path('<int:pk>/read/', views.NotificationMarkReadView.as_view(), name='read'),
]
