from django.urls import path
from . import views

app_name = 'ratings'

urlpatterns = [
    path('', views.RatingView.as_view(), name='my-ratings'),
    path('provider/<int:user_id>/', views.ProviderRatingView.as_view(), name='provider-ratings'),
]