"""
Crop Zoning API views.
No database. All responses are static mock data.
Response format: {"status": "success", "data": <payload>}. HTTP 200 only.
No processing, validation, or use of input parameters in responses.
"""

from django.core.exceptions import ImproperlyConfigured
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema

from config.swagger import status_response
from .mock_data import (
    AREA_RESPONSE_DATA,
    PRODUCTS_RESPONSE_DATA,
    ZONE_DETAILS_BY_ID,
    ZONES_CULTIVATION_RISK_RESPONSE_DATA,
    ZONES_INITIAL_RESPONSE_DATA,
    ZONES_SOIL_QUALITY_RESPONSE_DATA,
    ZONES_WATER_NEED_RESPONSE_DATA,
)
from .services import persist_zones


class AreaView(APIView):
    """
    GET endpoint for fixed land area (GeoJSON polygon).

    Purpose:
        Returns static land area polygon for display on map. User cannot
        draw or edit the region; it is loaded from backend.

    Input parameters:
        None.

    Response structure:
        - status: string, always "success".
        - data: object with key "area" (GeoJSON Feature with Polygon geometry).

    No processing or validation is performed on inputs.
    """

    @extend_schema(
        tags=["Crop Zoning"],
        responses={200: status_response("CropZoningAreaResponse", data=serializers.JSONField())},
    )
    def get(self, request):
        return Response(
            {"status": "success", "data": AREA_RESPONSE_DATA},
            status=status.HTTP_200_OK,
        )


class ProductsView(APIView):
    """
    GET endpoint for list of crop products and colors.

    Purpose:
        Returns static list of cultivable products with display color and
        Persian label for the Crop Zoning page (Legend and zone detail panel).
        Used when loading the crop-zoning page.

    Input parameters:
        - locale: string, optional. Location: query. Language code (e.g. fa, en).
          Not read or used in response.

    Response structure:
        - status: string, always "success".
        - data: object with key "products" (array of { id, label, color }).

    No processing or validation is performed on inputs.
    """

    @extend_schema(
        tags=["Crop Zoning"],
        responses={200: status_response("CropZoningProductsResponse", data=serializers.JSONField())},
    )
    def get(self, request):
        return Response(
            {"status": "success", "data": PRODUCTS_RESPONSE_DATA},
            status=status.HTTP_200_OK,
        )


class ZonesInitialView(APIView):
    """
    POST endpoint for initial zone data (map + hover/tooltip).

    Purpose:
        Accepts the main area polygon and creates zones based on configured
        area chunk size. Stores generated zones in database.

    Input parameters (body, JSON):
        - area: GeoJSON Feature. Location: body. Main land polygon.
          If omitted, the static area from mock data is used.

    Response structure:
        - status: string.
        - data: object with total_area_hectares, total_area_sqm, zone_count,
          chunk_area_sqm and zones.
    """

    @extend_schema(
        tags=["Crop Zoning"],
        request=OpenApiTypes.OBJECT,
        responses={200: status_response("CropZoningZonesInitialResponse", data=serializers.JSONField())},
    )
    def post(self, request):
        area_feature = request.data.get("area") or AREA_RESPONSE_DATA.get("area")

        try:
            zoning_result = persist_zones(area_feature)
        except ValueError as exc:
            return Response(
                {"status": "error", "message": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ImproperlyConfigured as exc:
            return Response(
                {"status": "error", "message": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        area_data = zoning_result["area"]
        response_data = {
            "area": {
                "id": area_data["id"],
                "uuid": area_data["uuid"],
                "geometry": area_data["geometry"],
                "points": area_data["points"],
                "center": area_data["center"],
                "area_sqm": round(area_data["area_sqm"], 2),
                "area_hectares": round(area_data["area_hectares"], 4),
                "chunk_area_sqm": round(area_data["chunk_area_sqm"], 2),
                "zone_count": area_data["zone_count"],
            },
            "zones": [
                {
                    "zoneId": zone["zone_id"],
                    "geometry": zone["geometry"],
                    "points": zone["points"],
                    "center": zone["center"],
                    "area_sqm": round(zone["area_sqm"], 2),
                    "area_hectares": round(zone["area_hectares"], 4),
                }
                for zone in zoning_result["zones"]
            ],
        }

        return Response(
            {"status": "success", "data": response_data},
            status=status.HTTP_200_OK,
        )



class ZonesWaterNeedView(APIView):
    """
    POST endpoint for water need per zone (water need layer).

    Purpose:
        Accepts zones (FeatureCollection) and returns static water need
        per zone for the water need map layer (level, value, color).

    Input parameters (body, JSON):
        - zones: GeoJSON FeatureCollection. Location: body.
        - products: array of strings, optional. Location: body. Not used.

    Response structure:
        - status: string, always "success".
        - data: object with zones (array of { zoneId, geometry, level, value, color }).

    No processing or validation is performed on inputs.
    """

    @extend_schema(
        tags=["Crop Zoning"],
        request=OpenApiTypes.OBJECT,
        responses={200: status_response("CropZoningZonesWaterNeedResponse", data=serializers.JSONField())},
    )
    def post(self, request):
        return Response(
            {"status": "success", "data": ZONES_WATER_NEED_RESPONSE_DATA},
            status=status.HTTP_200_OK,
        )


class ZonesSoilQualityView(APIView):
    """
    POST endpoint for soil quality per zone (soil quality layer).

    Purpose:
        Accepts zones (FeatureCollection) and returns static soil quality
        per zone for the soil quality map layer (level, score, color).

    Input parameters (body, JSON):
        - zones: GeoJSON FeatureCollection. Location: body.
        - products: array of strings, optional. Location: body. Not used.

    Response structure:
        - status: string, always "success".
        - data: object with zones (array of { zoneId, geometry, level, score, color }).

    No processing or validation is performed on inputs.
    """

    @extend_schema(
        tags=["Crop Zoning"],
        request=OpenApiTypes.OBJECT,
        responses={200: status_response("CropZoningZonesSoilQualityResponse", data=serializers.JSONField())},
    )
    def post(self, request):
        return Response(
            {"status": "success", "data": ZONES_SOIL_QUALITY_RESPONSE_DATA},
            status=status.HTTP_200_OK,
        )


class ZonesCultivationRiskView(APIView):
    """
    POST endpoint for cultivation risk per zone (cultivation risk layer).

    Purpose:
        Accepts zones (FeatureCollection) and returns static cultivation
        risk per zone for the risk map layer (level, color).

    Input parameters (body, JSON):
        - zones: GeoJSON FeatureCollection. Location: body.
        - products: array of strings, optional. Location: body. Not used.

    Response structure:
        - status: string, always "success".
        - data: object with zones (array of { zoneId, geometry, level, color }).

    No processing or validation is performed on inputs.
    """

    @extend_schema(
        tags=["Crop Zoning"],
        request=OpenApiTypes.OBJECT,
        responses={200: status_response("CropZoningZonesCultivationRiskResponse", data=serializers.JSONField())},
    )
    def post(self, request):
        return Response(
            {"status": "success", "data": ZONES_CULTIVATION_RISK_RESPONSE_DATA},
            status=status.HTTP_200_OK,
        )


class ZoneDetailsView(APIView):
    """
    GET endpoint for zone detail data (detail panel after click).

    Purpose:
        Returns static detail data for a single zone: reason, criteria,
        area_hectares for the detail panel and radar chart.

    Input parameters:
        - zoneId: string. Location: path. Zone identifier (e.g. zone-0).
          Not read or used in response.

    Response structure:
        - status: string, always "success".
        - data: object with zoneId, crop, matchPercent, waterNeed,
          estimatedProfit, reason, criteria (array), area_hectares.

    No processing or validation is performed on inputs. Input values are
    not used in the response.
    """

    @extend_schema(
        tags=["Crop Zoning"],
        responses={200: status_response("CropZoningZoneDetailsResponse", data=serializers.JSONField())},
    )
    def get(self, request, zone_id):
        data = ZONE_DETAILS_BY_ID.get(zone_id, ZONE_DETAILS_BY_ID["zone-0"])
        return Response(
            {"status": "success", "data": data},
            status=status.HTTP_200_OK,
        )
