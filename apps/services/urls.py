from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    path('', views.ServiceListView.as_view(), name='services'),
    path('vehicle-types/', views.VehicleTypeListView.as_view(), name='vehicle-types'),
    path('engine-types/', views.EngineTypeListView.as_view(), name='engine-types'),
    path('dirt-levels/', views.DirtLevelListView.as_view(), name='dirt-levels'),
]
