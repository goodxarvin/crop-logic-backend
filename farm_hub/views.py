from django.core.exceptions import ImproperlyConfigured
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from config.swagger import code_response
from .models import FarmHub
from .serializers import FarmHubCreateSerializer, FarmHubSerializer, FarmToggleSerializer
from .services import create_farm_with_zoning


class FarmHubBaseView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_farm(self, request, farm_uuid):
        try:
            return FarmHub.objects.prefetch_related("products", "sensors").select_related("farm_type").get(
                farm_uuid=farm_uuid,
                owner=request.user,
            )
        except FarmHub.DoesNotExist:
            return None


class FarmListCreateView(FarmHubBaseView):
    @extend_schema(
        tags=["Farm Hub"],
        responses={200: code_response("FarmListResponse", data=FarmHubSerializer(many=True))},
    )
    def get(self, request):
        farms = FarmHub.objects.filter(owner=request.user).select_related("farm_type").prefetch_related(
            "products",
            "sensors",
        )
        data = FarmHubSerializer(farms, many=True).data
        return Response({"code": 200, "msg": "success", "data": data}, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Farm Hub"],
        request=FarmHubCreateSerializer,
        responses={201: code_response("FarmCreateResponse", data=FarmHubSerializer())},
    )
    def post(self, request):
        serializer = FarmHubCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            farm, zoning_payload = create_farm_with_zoning(serializer, owner=request.user)
        except ValueError as exc:
            raise serializers.ValidationError({"area_geojson": [str(exc)]}) from exc
        except ImproperlyConfigured as exc:
            return Response({"code": 500, "msg": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = FarmHubSerializer(farm).data
        if zoning_payload is not None:
            data["zoning"] = zoning_payload
        return Response({"code": 201, "msg": "success", "data": data}, status=status.HTTP_201_CREATED)


class FarmDetailView(FarmHubBaseView):
    @extend_schema(
        tags=["Farm Hub"],
        responses={
            200: code_response("FarmDetailResponse", data=FarmHubSerializer()),
            404: code_response("FarmNotFoundResponse"),
        },
    )
    def get(self, request, farm_uuid):
        farm = self._get_farm(request, farm_uuid)
        if farm is None:
            return Response({"code": 404, "msg": "Farm not found."}, status=status.HTTP_404_NOT_FOUND)
        data = FarmHubSerializer(farm).data
        return Response({"code": 200, "msg": "success", "data": data}, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Farm Hub"],
        request=FarmHubCreateSerializer,
        responses={
            200: code_response("FarmUpdateResponse", data=FarmHubSerializer()),
            404: code_response("FarmUpdateNotFoundResponse"),
        },
    )
    def patch(self, request, farm_uuid):
        farm = self._get_farm(request, farm_uuid)
        if farm is None:
            return Response({"code": 404, "msg": "Farm not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = FarmHubCreateSerializer(farm, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        farm.refresh_from_db()
        data = FarmHubSerializer(farm).data
        return Response({"code": 200, "msg": "success", "data": data}, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Farm Hub"],
        responses={
            200: code_response("FarmDeleteResponse"),
            404: code_response("FarmDeleteNotFoundResponse"),
        },
    )
    def delete(self, request, farm_uuid):
        farm = self._get_farm(request, farm_uuid)
        if farm is None:
            return Response({"code": 404, "msg": "Farm not found."}, status=status.HTTP_404_NOT_FOUND)
        farm.delete()
        return Response({"code": 200, "msg": "success"}, status=status.HTTP_200_OK)


class FarmToggleView(FarmHubBaseView):
    action = None

    @extend_schema(
        tags=["Farm Hub"],
        request=FarmToggleSerializer,
        responses={
            200: code_response("FarmToggleResponse"),
            400: code_response("FarmToggleValidationResponse"),
            404: code_response("FarmToggleNotFoundResponse"),
        },
    )
    def post(self, request):
        serializer = FarmToggleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        farm = self._get_farm(request, serializer.validated_data["farm_uuid"])
        if farm is None:
            return Response({"code": 404, "msg": "Farm not found."}, status=status.HTTP_404_NOT_FOUND)

        farm.is_active = self.action == "active"
        farm.save(update_fields=["is_active", "updated_at"])
        return Response({"code": 200, "msg": "success"}, status=status.HTTP_200_OK)


class FarmActiveView(FarmToggleView):
    action = "active"


class FarmDeactiveView(FarmToggleView):
    action = "deactive"
