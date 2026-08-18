from django.urls import path
from . import views
from .views import (
    AppSettingListCreateView,
    AppSettingDetailView,
    PublicAppSettingListView,
    PublicAppSettingDetailView,
)

app_name = 'services'

urlpatterns = [
    path('', views.ServiceListView.as_view(), name='services'),
    path('vehicle-types/', views.VehicleTypeListView.as_view(), name='vehicle-types'),
    path('engine-types/', views.EngineTypeListView.as_view(), name='engine-types'),
    path('dirt-levels/', views.DirtLevelListView.as_view(), name='dirt-levels'),
    path('seed-data/', views.SeedDataView.as_view(), name='seed-data'),
]

urlpatterns = urlpatterns + [
    path('settings/public/', PublicAppSettingListView.as_view(), name='app-setting-public-list'),
    path('settings/public/<str:settings_type>/', PublicAppSettingDetailView.as_view(), name='app-setting-public-detail'),
    path('settings/', AppSettingListCreateView.as_view(), name='app-setting-list'),
    path('settings/<int:pk>/', AppSettingDetailView.as_view(), name='app-setting-detail'),
]