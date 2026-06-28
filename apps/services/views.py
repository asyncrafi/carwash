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


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.shortcuts import get_object_or_404

from .models import AppSetting
from .serializers import AppSettingSerializer


class AppSettingListCreateView(APIView):
    """
    GET  /settings/          → anyone can list (global settings)
    POST /settings/          → admin only
    """

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]

    def get(self, request):
        settings_type = request.query_params.get('type')  # ?type=privacy
        qs = AppSetting.objects.filter(user=None)          # global only
        if settings_type:
            qs = qs.filter(settings_type=settings_type)
        serializer = AppSettingSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = AppSettingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AppSettingDetailView(APIView):
    """
    GET    /settings/<pk>/   → anyone
    PUT    /settings/<pk>/   → admin only
    PATCH  /settings/<pk>/   → admin only
    DELETE /settings/<pk>/   → admin only
    """

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]

    def get_object(self, pk):
        return get_object_or_404(AppSetting, pk=pk)

    def get(self, request, pk):
        setting = self.get_object(pk)
        serializer = AppSettingSerializer(setting)
        return Response(serializer.data)

    def put(self, request, pk):
        setting = self.get_object(pk)
        serializer = AppSettingSerializer(setting, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        setting = self.get_object(pk)
        serializer = AppSettingSerializer(setting, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        setting = self.get_object(pk)
        setting.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)  