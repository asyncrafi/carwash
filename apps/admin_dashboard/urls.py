from django.urls import path
from . import views


app_name = 'admin_dashboard'

urlpatterns = [
    path('dashboard/', views.AdminDashboardView.as_view(), name='dashboard'),
    path('users/', views.AdminUserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', views.AdminUserDetailView.as_view(), name='user-detail'),
    path('users/<int:pk>/block/', views.AdminUserBlockView.as_view(), name='user-block'),
    path('users/<int:pk>/unblock/', views.AdminUserUnblockView.as_view(), name='user-unblock'),
    path('providers/<int:provider_pk>/documents/', views.AdminProviderDocumentListView.as_view(), name='provider-docs'),
    path('documents/<int:pk>/review/', views.AdminDocumentReviewView.as_view(), name='doc-review'),
    path('providers/<int:pk>/approve/', views.AdminProviderApproveView.as_view(), name='provider-approve'),
    path('providers/<int:pk>/reject/', views.AdminProviderRejectView.as_view(), name='provider-reject'),
    path('bookings/', views.AdminBookingListView.as_view(), name='booking-list'),
    path('bookings/<int:pk>/', views.AdminBookingDetailView.as_view(), name='booking-detail'),
    path('bookings/<int:pk>/cancel/', views.AdminBookingCancelView.as_view(), name='booking-cancel'),
    path('earnings/', views.AdminEarningsDashboardView.as_view(), name='earnings'),
    path('payouts/', views.AdminPayoutsListView.as_view(), name='payouts-list'),
    path('payouts/<int:pk>/retry/', views.AdminPayoutRetryView.as_view(), name='payouts-retry'),
    path('services/', views.AdminServiceListCreateView.as_view(), name='services'),
    path('services/<int:pk>/', views.AdminServiceDetailView.as_view(), name='service-detail'),
    path('config/', views.AdminPlatformConfigView.as_view(), name='config'),
    path('notifications/send/', views.AdminSendNotificationView.as_view(), name='notif-send'),

    # ─── Vehicle & Engine & Dirt ────────────────────────────
    path('vehicle-types/', views.VehicleTypeListCreateView.as_view(), name='vehicle-type-list'),
    path('vehicle-types/<int:pk>/', views.VehicleTypeDetailView.as_view(), name='vehicle-type-detail'),
    path('engine-types/', views.EngineTypeListCreateView.as_view(), name='engine-type-list'),
    path('engine-types/<int:pk>/', views.EngineTypeDetailView.as_view(), name='engine-type-detail'),
    path('dirt-levels/', views.DirtLevelListCreateView.as_view(), name='dirt-level-list'),
    path('dirt-levels/<int:pk>/', views.DirtLevelDetailView.as_view(), name='dirt-level-detail'),

]