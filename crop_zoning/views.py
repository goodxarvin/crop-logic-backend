"""
Crop Zoning API views.
Plain Django only; no DRF. No database. All responses are static mock data.
Response format: {"status": "success", "data": <payload>}. HTTP 200 only.
No processing, validation, or use of input parameters in responses.
CSRF exempt on POST so frontend can call without token.
"""

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .mock_data import (
    AREA_RESPONSE_DATA,
    PRODUCTS_RESPONSE_DATA,
    ZONE_DETAILS_BY_ID,
    ZONES_CULTIVATION_RISK_RESPONSE_DATA,
    ZONES_INITIAL_RESPONSE_DATA,
    ZONES_SOIL_QUALITY_RESPONSE_DATA,
    ZONES_WATER_NEED_RESPONSE_DATA,
)


class AreaView(View):
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

    def get(self, request):
        return JsonResponse(
            {"status": "success", "data": AREA_RESPONSE_DATA},
            status=200,
        )


class ProductsView(View):
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

    def get(self, request):
        return JsonResponse(
            {"status": "success", "data": PRODUCTS_RESPONSE_DATA},
            status=200,
        )


@method_decorator(csrf_exempt, name="dispatch")
class ZonesInitialView(View):
    """
    POST endpoint for initial zone data (map + hover/tooltip).

    Purpose:
        Accepts zones (FeatureCollection of grid squares) and returns static
        initial data per zone for map rendering and hover/tooltip display.
        Does not include reason or criteria (those are in zone details).

    Input parameters (body, JSON):
        - zones: GeoJSON FeatureCollection. Location: body. Grid square polygons.
        - products: array of strings, optional. Location: body. Product IDs.
          Not read or used in response.

    Response structure:
        - status: string, always "success".
        - data: object with total_area_hectares, total_area_sqm, zone_count,
          zones (array of { zoneId, geometry, crop, matchPercent, waterNeed,
          estimatedProfit }).

    No processing or validation is performed on inputs. Input values are
    not used in the response.
    """

    def post(self, request):
        return JsonResponse(
            {"status": "success", "data": ZONES_INITIAL_RESPONSE_DATA},
            status=200,
        )


@method_decorator(csrf_exempt, name="dispatch")
class ZonesWaterNeedView(View):
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

    def post(self, request):
        return JsonResponse(
            {"status": "success", "data": ZONES_WATER_NEED_RESPONSE_DATA},
            status=200,
        )


@method_decorator(csrf_exempt, name="dispatch")
class ZonesSoilQualityView(View):
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

    def post(self, request):
        return JsonResponse(
            {"status": "success", "data": ZONES_SOIL_QUALITY_RESPONSE_DATA},
            status=200,
        )


@method_decorator(csrf_exempt, name="dispatch")
class ZonesCultivationRiskView(View):
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

    def post(self, request):
        return JsonResponse(
            {"status": "success", "data": ZONES_CULTIVATION_RISK_RESPONSE_DATA},
            status=200,
        )


class ZoneDetailsView(View):
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

    def get(self, request, zone_id):
        data = ZONE_DETAILS_BY_ID.get(zone_id, ZONE_DETAILS_BY_ID["zone-0"])
        return JsonResponse(
            {"status": "success", "data": data},
            status=200,
        )
