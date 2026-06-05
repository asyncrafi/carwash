from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.core.mixins import BaseResponseMixin
from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(user=request.user)
        data = NotificationSerializer(notifications, many=True).data
        return self.success_response(data=data)


class NotificationMarkReadView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        notif = get_object_or_404(Notification, pk=pk, user=request.user)
        notif.is_read = True
        notif.save()
        return self.success_response(message="Notification marked as read.")


class NotificationMarkAllReadView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        Notification.objects.filter(
            user=request.user, is_read=False
        ).update(is_read=True)
        return self.success_response(
            message="All notifications marked as read."
        )
