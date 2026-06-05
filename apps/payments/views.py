from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.core.mixins import BaseResponseMixin
from apps.providers.models import ProviderProfile
from .models import ProviderEarning
from .serializers import ProviderEarningSerializer


class ProviderEarningsView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = get_object_or_404(ProviderProfile, user=request.user)
        earnings = ProviderEarning.objects.filter(
            provider=profile
        ).order_by('-created_at')
        total = earnings.aggregate(
            total=Sum('net_amount')
        )['total'] or 0
        today = earnings.filter(
            created_at__date=timezone.now().date()
        ).aggregate(today=Sum('net_amount'))['today'] or 0
        jobs_total = earnings.count()

        data = {
            'total_balance': float(total),
            'today_earnings': float(today),
            'jobs_total': jobs_total,
            'earnings': ProviderEarningSerializer(earnings, many=True).data,
        }
        return self.success_response(data=data)
