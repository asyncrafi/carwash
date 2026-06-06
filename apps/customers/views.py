from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.core.mixins import BaseResponseMixin
from .models import CustomerProfile, SavedAddress, PaymentCard, Vehicle
from .serializers import (
    CustomerProfileSerializer,
    SavedAddressSerializer,
    PaymentCardSerializer,
    VehicleSerializer,
)


class CustomerProfileView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = get_object_or_404(CustomerProfile, user=request.user)
        data = CustomerProfileSerializer(profile, context={'request': request}).data
        return self.success_response(data=data)


class SavedAddressListCreateView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = get_object_or_404(CustomerProfile, user=request.user)
        addresses = SavedAddress.objects.filter(customer=profile)
        data = SavedAddressSerializer(addresses, many=True).data
        return self.success_response(data=data)

    def post(self, request):
        profile = get_object_or_404(CustomerProfile, user=request.user)
        serializer = SavedAddressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data.get('is_default'):
            SavedAddress.objects.filter(customer=profile).update(is_default=False)
        serializer.save(customer=profile)
        return self.created_response(data=serializer.data)


class SavedAddressDetailView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, request):
        profile = get_object_or_404(CustomerProfile, user=request.user)
        return get_object_or_404(SavedAddress, pk=pk, customer=profile)

    def get(self, request, pk):
        data = SavedAddressSerializer(self.get_object(pk, request)).data
        return self.success_response(data=data)

    def patch(self, request, pk):
        obj = self.get_object(pk, request)
        serializer = SavedAddressSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data.get('is_default'):
            SavedAddress.objects.filter(customer=obj.customer).exclude(pk=obj.pk).update(is_default=False)
        serializer.save()
        return self.updated_response(data=serializer.data)

    def delete(self, request, pk):
        self.get_object(pk, request).delete()
        return self.deleted_response(message="Address deleted successfully.")


class PaymentCardListCreateView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = get_object_or_404(CustomerProfile, user=request.user)
        cards = PaymentCard.objects.filter(customer=profile)
        data = PaymentCardSerializer(cards, many=True).data
        return self.success_response(data=data)

    def post(self, request):
        profile = get_object_or_404(CustomerProfile, user=request.user)
        serializer = PaymentCardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data.get('is_default'):
            PaymentCard.objects.filter(customer=profile).update(is_default=False)
        serializer.save(customer=profile)
        return self.created_response(data=serializer.data)


class PaymentCardDetailView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, request):
        profile = get_object_or_404(CustomerProfile, user=request.user)
        return get_object_or_404(PaymentCard, pk=pk, customer=profile)

    def delete(self, request, pk):
        self.get_object(pk, request).delete()
        return self.deleted_response(message="Payment card removed successfully.")

    def patch(self, request, pk):
        obj = self.get_object(pk, request)
        serializer = PaymentCardSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.updated_response(data=serializer.data)


class VehicleListCreateView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = get_object_or_404(CustomerProfile, user=request.user)
        vehicles = Vehicle.objects.filter(customer=profile)
        data = VehicleSerializer(vehicles, many=True).data
        return self.success_response(data=data)

    def post(self, request):
        profile = get_object_or_404(CustomerProfile, user=request.user)
        serializer = VehicleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(customer=profile)
        return self.created_response(data=serializer.data)


class VehicleDetailView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, request):
        profile = get_object_or_404(CustomerProfile, user=request.user)
        return get_object_or_404(Vehicle, pk=pk, customer=profile)

    def get(self, request, pk):
        data = VehicleSerializer(self.get_object(pk, request)).data
        return self.success_response(data=data)

    def patch(self, request, pk):
        obj = self.get_object(pk, request)
        serializer = VehicleSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.updated_response(data=serializer.data)

    def delete(self, request, pk):
        self.get_object(pk, request).delete()
        return self.deleted_response(message="Vehicle removed successfully.")
