from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from apps.core.mixins import BaseResponseMixin
from .models import Rating
from .serializers import RatingSerializer


class RatingView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ratings = Rating.objects.filter(reviewee=request.user)
        data = RatingSerializer(ratings, many=True, context={'request': request}).data
        return self.success_response(data=data)
