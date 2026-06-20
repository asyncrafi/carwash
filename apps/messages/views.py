from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.core.mixins import BaseResponseMixin
from .models import ChatMessage, CallLog
from .serializers import ChatMessageSerializer, CallLogSerializer


class ChatMessageListCreateView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, booking_pk=None, other_user_id=None):
        # list messages for a booking or between users
        qs = ChatMessage.objects.all()
        if booking_pk:
            qs = qs.filter(booking_id=booking_pk)
        elif other_user_id:
            qs = qs.filter(sender=request.user).filter(recipient_id=other_user_id) | qs.filter(sender_id=other_user_id, recipient=request.user)
        qs = qs.order_by('created_at')
        data = ChatMessageSerializer(qs, many=True).data
        return self.success_response(data=data)

    def post(self, request):
        serializer = ChatMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(sender=request.user)
        return self.created_response(data=serializer.data)


class CallLogCreateView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CallLogSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(caller=request.user)
        return self.created_response(data=serializer.data)
