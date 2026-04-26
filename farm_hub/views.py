from django.db import transaction
from django.core.exceptions import ImproperlyConfigured
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema

from config.swagger import code_response
from .models import FarmHub, FarmType, Product
from .serializers import (
    FarmHubCreateSerializer,
    FarmHubSerializer,
    FarmToggleSerializer,
    FarmTypeSerializer,
    ProductSerializer,
)
from .services import FarmDataSyncError, create_farm_with_zoning, dispatch_farm_zoning, sync_farm_data


class FarmHubBaseView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_farm(self, request, farm_uuid):
        try:
            return FarmHub.objects.prefetch_related("products", "sensors", "sensors__sensor_catalog").select_related(
                "farm_type",
                "subscription_plan",
                "current_crop_area",
            ).get(
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
        farms = FarmHub.objects.filter(owner=request.user).select_related(
            "farm_type",
            "subscription_plan",
            "current_crop_area",
        ).prefetch_related(
            "products",
            "sensors",
            "sensors__sensor_catalog",
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
        except FarmDataSyncError as exc:
            return Response({"code": 502, "msg": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        except ImproperlyConfigured as exc:
            return Response({"code": 500, "msg": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = FarmHubSerializer(farm).data
        if zoning_payload is not None:
            data["zoning"] = zoning_payload
        return Response({"code": 201, "msg": "success", "data": data}, status=status.HTTP_201_CREATED)


class FarmTypeListView(FarmHubBaseView):
    @extend_schema(
        tags=["Farm Hub"],
        responses={200: code_response("FarmTypeListResponse", data=FarmTypeSerializer(many=True))},
    )
    def get(self, request):
        farm_types = FarmType.objects.order_by("name")
        data = FarmTypeSerializer(farm_types, many=True).data
        return Response({"code": 200, "msg": "success", "data": data}, status=status.HTTP_200_OK)


class FarmTypeProductsView(FarmHubBaseView):
    @extend_schema(
        tags=["Farm Hub"],
        responses={
            200: code_response("FarmTypeProductsResponse", data=ProductSerializer(many=True)),
            404: code_response("FarmTypeProductsNotFoundResponse"),
        },
    )
    def get(self, request, farm_type_uuid):
        try:
            farm_type = FarmType.objects.get(uuid=farm_type_uuid)
        except FarmType.DoesNotExist:
            return Response({"code": 404, "msg": "Farm type not found."}, status=status.HTTP_404_NOT_FOUND)

        products = Product.objects.filter(farm_type=farm_type).order_by("name")
        data = ProductSerializer(products, many=True).data
        return Response({"code": 200, "msg": "success", "data": data}, status=status.HTTP_200_OK)


class FarmDetailView(FarmHubBaseView):
    @extend_schema(
        tags=["Farm Hub"],
        parameters=[
            OpenApiParameter(name="farm_uuid", type=OpenApiTypes.UUID, location=OpenApiParameter.PATH, default="11111111-1111-1111-1111-111111111111"),
        ],
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
        parameters=[
            OpenApiParameter(name="farm_uuid", type=OpenApiTypes.UUID, location=OpenApiParameter.PATH, default="11111111-1111-1111-1111-111111111111"),
        ],
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
        area_feature = serializer.validated_data.get("area_geojson", None)
        sensor_key = serializer.validated_data.get("sensor_key", "sensor-7-1")
        sensor_payload = serializer.validated_data.get("sensor_payload", None)
        irrigation_method_id = serializer.validated_data.get("irrigation_method_id", None)
        try:
            with transaction.atomic():
                serializer.save()
                if area_feature is not None:
                    crop_area, _zoning_payload = dispatch_farm_zoning(area_feature, serializer.instance)
                    serializer.instance.current_crop_area = crop_area
                    serializer.instance.save(update_fields=["current_crop_area", "updated_at"])
                sync_farm_data(
                    farm=serializer.instance,
                    area_feature=area_feature,
                    sensor_key=sensor_key,
                    sensor_payload=sensor_payload,
                    plant_ids=[product.id for product in serializer.instance.products.all()],
                    irrigation_method_id=irrigation_method_id,
                )
        except FarmDataSyncError as exc:
            return Response({"code": 502, "msg": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        farm.refresh_from_db()
        data = FarmHubSerializer(farm).data
        return Response({"code": 200, "msg": "success", "data": data}, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Farm Hub"],
        parameters=[
            OpenApiParameter(name="farm_uuid", type=OpenApiTypes.UUID, location=OpenApiParameter.PATH, default="11111111-1111-1111-1111-111111111111"),
        ],
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
