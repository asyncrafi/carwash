from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.core.mixins import BaseResponseMixin
from apps.bookings.models import Booking
from .models import ChatMessage, CallLog
from .serializers import ChatMessageSerializer, CallLogSerializer


class ChatMessageListCreateView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, booking_pk=None, other_user_id=None):
        qs = ChatMessage.objects.all()

        if booking_pk:
            booking = get_object_or_404(Booking, pk=booking_pk)
            user = request.user
            is_customer = (
                hasattr(user, 'customer_profile') and
                booking.customer == user.customer_profile
            )
            is_provider = (
                hasattr(user, 'provider_profile') and
                booking.provider == user.provider_profile
            )
            if not (is_customer or is_provider):
                return self.error_response(
                    message="You don't have access to this booking's messages."
                )
            qs = qs.filter(booking_id=booking_pk)

        elif other_user_id:
            qs = (
                qs.filter(sender=request.user, recipient_id=other_user_id) |
                qs.filter(sender_id=other_user_id, recipient=request.user)
            )

        qs = qs.order_by('created_at')
        data = ChatMessageSerializer(
            qs, many=True, context={'request': request}
        ).data
        return self.success_response(data=data)

    def post(self, request):
        serializer = ChatMessageSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(sender=request.user)
        return self.created_response(data=serializer.data)


class CallLogCreateView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CallLogSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(caller=request.user)
        return self.created_response(data=serializer.data)