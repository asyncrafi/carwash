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


from django.db.models import Q

class ServiceListView(BaseResponseMixin, APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        services = Service.objects.filter(is_active=True)
        vehicle_type_id = request.query_params.get('vehicle_type')
        engine_type_id = request.query_params.get('engine_type')

        if vehicle_type_id:
            services = services.filter(Q(vehicle_type_id=vehicle_type_id) | Q(vehicle_type__isnull=True))
        if engine_type_id:
            services = services.filter(Q(engine_type_id=engine_type_id) | Q(engine_type__isnull=True))

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
