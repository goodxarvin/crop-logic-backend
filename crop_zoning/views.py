"""
Crop Zoning API views.
Plain Django only; no DRF. No database. All responses are static mock data.
Response format: {"status": "success", "data": <payload>}. HTTP 200 only.
No processing, validation, or use of input parameters in responses.
"""

from django.http import JsonResponse
from django.views import View

from .mock_data import INITIAL_REGION_RESPONSE, OPTIMIZE_ZONING_RESPONSE


class OptimizeZoningView(View):
    """
    POST endpoint for zoning optimization.

    Purpose:
        Returns a static GeoJSON FeatureCollection of zones with crop suggestions
        (API_RESPONSE_SPEC §1). Used when the user selects a region on the map
        and triggers "optimize zoning". No processing is performed on the request.

    Input parameters:
        - body (optional): JSON body; may contain a GeoJSON Feature with Polygon.
          Data type: object. Location: body. Not read or validated; not used in response.

    Response structure:
        - status: string, always "success".
        - data: object, GeoJSON FeatureCollection with features containing
          geometry (Polygon) and properties (zoneId, crop, matchPercent, waterNeed,
          estimatedProfit, reason, criteria).

    No processing or validation is performed on inputs.
    """

    def post(self, request):
        return JsonResponse(
            {"status": "success", "data": OPTIMIZE_ZONING_RESPONSE},
            status=200,
        )


class InitialRegionView(View):
    """
    GET endpoint for the initial map region.

    Purpose:
        Returns a static GeoJSON Feature with Polygon defining the initial
        map region (API_RESPONSE_SPEC §2). Optional; used when the initial
        region is loaded from the server instead of a fixed client mock.

    Input parameters:
        None. Query parameters, if sent, are not read or used.

    Response structure:
        - status: string, always "success".
        - data: object, GeoJSON Feature with geometry.type "Polygon" and
          coordinates as [longitude, latitude]; first and last point equal.

    No processing or validation is performed on inputs.
    """

    def get(self, request):
        return JsonResponse(
            {"status": "success", "data": INITIAL_REGION_RESPONSE},
            status=200,
        )
