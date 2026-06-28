from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from urllib3 import request
from apps.accounts.views import User
from apps.accounts.models import User

from apps.core.mixins import BaseResponseMixin
from .models import Rating
from .serializers import RatingSerializer


class RatingView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role == User.ROLE_PROVIDER:
            # Provider sees ratings received about them
            ratings = Rating.objects.filter(reviewee=user)
        elif user.role == User.ROLE_CUSTOMER:
            # Customer sees ratings they gave
            ratings = Rating.objects.filter(reviewer=user)
        else:
            # Admin sees all
            ratings = Rating.objects.all()

        data = RatingSerializer(ratings, many=True, context={'request': request}).data
        return self.success_response(data=data)



from apps.providers.models import ProviderProfile

class ProviderRatingView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        ratings = Rating.objects.filter(
            reviewee_id=user_id
        ).select_related('reviewer').order_by('-created_at')

        if not ratings.exists():
            return self.success_response(data={
                'average_rating': 0,
                'total_reviews': 0,
                'reviews': [],
            })

        from django.db.models import Avg
        summary = ratings.aggregate(average=Avg('stars'))
        data = RatingSerializer(ratings, many=True, context={'request': request}).data

        return self.success_response(data={
            'average_rating': round(summary['average'] or 0, 2),
            'total_reviews': ratings.count(),
            'reviews': data,
        })