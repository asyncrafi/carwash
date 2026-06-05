from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.core.mixins import BaseResponseMixin
from .models import Service, VehicleType, EngineType, DirtLevel
from .serializers import (
    ServiceSerializer,
    VehicleTypeSerializer,
    EngineTypeSerializer,
    DirtLevelSerializer,
)


class ServiceListView(BaseResponseMixin, APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        services = Service.objects.filter(is_active=True)
        data = ServiceSerializer(services, many=True).data
        return self.success_response(data=data)


class VehicleTypeListView(BaseResponseMixin, APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        types = VehicleType.objects.filter(is_active=True)
        data = VehicleTypeSerializer(types, many=True).data
        return self.success_response(data=data)


class EngineTypeListView(BaseResponseMixin, APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        types = EngineType.objects.all()
        data = EngineTypeSerializer(types, many=True).data
        return self.success_response(data=data)


class DirtLevelListView(BaseResponseMixin, APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        levels = DirtLevel.objects.all()
        data = DirtLevelSerializer(levels, many=True).data
        return self.success_response(data=data)
