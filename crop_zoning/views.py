from django.core.exceptions import ImproperlyConfigured
from django.http import Http404
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from config.swagger import status_response
from .services import (
    create_zones_and_dispatch,
    ensure_latest_area_ready_for_processing,
    get_latest_cultivation_risk_payload,
    get_cultivation_risk_payload,
    get_default_area_feature,
    get_initial_zones_payload,
    get_latest_area_payload,
    get_latest_soil_quality_payload,
    get_latest_water_need_payload,
    get_products_payload,
    get_soil_quality_payload,
    get_water_need_payload,
    get_zone_details_payload,
    get_zone_page_request_params,
)


AREA_QUERY_PARAMETERS = [
    OpenApiParameter(
        name="farm_uuid",
        type=OpenApiTypes.UUID,
        location=OpenApiParameter.QUERY,
        required=True,
        description="UUID مزرعه برای گرفتن يا ساخت آخرين پردازش محدوده همان مزرعه.",
        default="11111111-1111-1111-1111-111111111111"),
    OpenApiParameter(
        name="page",
        type=OpenApiTypes.INT,
        location=OpenApiParameter.QUERY,
        required=False,
        description="شماره صفحه زون ها. مقدار پيش فرض 1 است.",
    ),
    OpenApiParameter(
        name="page_size",
        type=OpenApiTypes.INT,
        location=OpenApiParameter.QUERY,
        required=False,
        description="تعداد زون در هر صفحه. مقدار پيش فرض 10 است.",
    ),
]


class BaseAreaDataView(APIView):
    payload_getter = None

    def get(self, request):
        farm_uuid = request.query_params.get("farm_uuid")
        try:
            page, page_size = get_zone_page_request_params(request.query_params)
            crop_area = ensure_latest_area_ready_for_processing(farm_uuid=farm_uuid, owner=request.user)
        except ValueError as exc:
            return Response({"status": "error", "message": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except ImproperlyConfigured as exc:
            return Response({"status": "error", "message": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(
            {"status": "success", "data": self.payload_getter(crop_area, page=page, page_size=page_size)},
            status=status.HTTP_200_OK,
        )


class AreaView(BaseAreaDataView):
    payload_getter = staticmethod(get_latest_area_payload)

    @extend_schema(
        tags=["Crop Zoning"],
        parameters=AREA_QUERY_PARAMETERS,
        responses={
            200: status_response("CropZoningAreaResponse", data=serializers.JSONField()),
            400: status_response("CropZoningAreaValidationError", data=serializers.JSONField()),
            500: status_response("CropZoningAreaServerError", data=serializers.JSONField()),
        },
    )
    def get(self, request):
        return super().get(request)


class WaterNeedView(BaseAreaDataView):
    payload_getter = staticmethod(get_latest_water_need_payload)

    @extend_schema(
        tags=["Crop Zoning"],
        parameters=AREA_QUERY_PARAMETERS,
        responses={
            200: status_response("CropZoningWaterNeedResponse", data=serializers.JSONField()),
            400: status_response("CropZoningWaterNeedValidationError", data=serializers.JSONField()),
            500: status_response("CropZoningWaterNeedServerError", data=serializers.JSONField()),
        },
    )
    def get(self, request):
        return super().get(request)


class SoilQualityView(BaseAreaDataView):
    payload_getter = staticmethod(get_latest_soil_quality_payload)

    @extend_schema(
        tags=["Crop Zoning"],
        parameters=AREA_QUERY_PARAMETERS,
        responses={
            200: status_response("CropZoningSoilQualityResponse", data=serializers.JSONField()),
            400: status_response("CropZoningSoilQualityValidationError", data=serializers.JSONField()),
            500: status_response("CropZoningSoilQualityServerError", data=serializers.JSONField()),
        },
    )
    def get(self, request):
        return super().get(request)


class CultivationRiskView(BaseAreaDataView):
    payload_getter = staticmethod(get_latest_cultivation_risk_payload)

    @extend_schema(
        tags=["Crop Zoning"],
        parameters=AREA_QUERY_PARAMETERS,
        responses={
            200: status_response("CropZoningCultivationRiskResponse", data=serializers.JSONField()),
            400: status_response("CropZoningCultivationRiskValidationError", data=serializers.JSONField()),
            500: status_response("CropZoningCultivationRiskServerError", data=serializers.JSONField()),
        },
    )
    def get(self, request):
        return super().get(request)


class ProductsView(APIView):
    @extend_schema(
        tags=["Crop Zoning"],
        responses={200: status_response("CropZoningProductsResponse", data=serializers.JSONField())},
    )
    def get(self, request):
        return Response({"status": "success", "data": get_products_payload()}, status=status.HTTP_200_OK)


class ZonesInitialView(APIView):
    @extend_schema(
        tags=["Crop Zoning"],
        request=OpenApiTypes.OBJECT,
        responses={200: status_response("CropZoningZonesInitialResponse", data=serializers.JSONField())},
    )
    def post(self, request):
        area_feature = (
            request.data.get("area")
            or request.data.get("area_geojson")
            or request.data.get("boundary")
            or get_default_area_feature()
        )
        cell_side_km = request.data.get("cell_side_km")

        try:
            crop_area, _zones = create_zones_and_dispatch(area_feature, cell_side_km=cell_side_km)
        except ValueError as exc:
            return Response({"status": "error", "message": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except ImproperlyConfigured as exc:
            return Response({"status": "error", "message": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"status": "success", "data": get_initial_zones_payload(crop_area)}, status=status.HTTP_200_OK)


class ZonesWaterNeedView(APIView):
    @extend_schema(
        tags=["Crop Zoning"],
        request=OpenApiTypes.OBJECT,
        responses={200: status_response("CropZoningZonesWaterNeedResponse", data=serializers.JSONField())},
    )
    def post(self, request):
        zone_ids = request.data.get("zoneIds")
        return Response({"status": "success", "data": get_water_need_payload(zone_ids)}, status=status.HTTP_200_OK)


class ZonesSoilQualityView(APIView):
    @extend_schema(
        tags=["Crop Zoning"],
        request=OpenApiTypes.OBJECT,
        responses={200: status_response("CropZoningZonesSoilQualityResponse", data=serializers.JSONField())},
    )
    def post(self, request):
        zone_ids = request.data.get("zoneIds")
        return Response({"status": "success", "data": get_soil_quality_payload(zone_ids)}, status=status.HTTP_200_OK)


class ZonesCultivationRiskView(APIView):
    @extend_schema(
        tags=["Crop Zoning"],
        request=OpenApiTypes.OBJECT,
        responses={200: status_response("CropZoningZonesCultivationRiskResponse", data=serializers.JSONField())},
    )
    def post(self, request):
        zone_ids = request.data.get("zoneIds")
        return Response({"status": "success", "data": get_cultivation_risk_payload(zone_ids)}, status=status.HTTP_200_OK)


class ZoneDetailsView(APIView):
    @extend_schema(
        tags=["Crop Zoning"],
        responses={200: status_response("CropZoningZoneDetailsResponse", data=serializers.JSONField())},
    )
    def get(self, request, zone_id):
        try:
            data = get_zone_details_payload(zone_id)
        except Exception as exc:
            if exc.__class__.__name__ == "DoesNotExist":
                raise Http404("Zone not found")
            raise
        return Response({"status": "success", "data": data}, status=status.HTTP_200_OK)
