"""
Irrigation Recommendation API views.
Plain Django only; no DRF. No database. All responses are static mock data.
Response format: {"status": "success", "data": <payload>}. HTTP 200 only.
No processing, validation, or use of input parameters in responses.
CSRF exempt on POST so frontend can call without token.
"""

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .mock_data import CONFIG_RESPONSE_DATA, RECOMMEND_RESPONSE_DATA


class ConfigView(View):
    """
    GET endpoint for irrigation config (farm info and crop options).

    Purpose:
        Returns static farm info (soilType, waterQuality, climateZone) and
        crop options list for the irrigation recommendation form. Used when
        loading the irrigation recommendation page.

    Input parameters:
        None. Query parameters, if sent, are not read or used.

    Response structure:
        - status: string, always "success".
        - data: object with keys farmInfo (object), cropOptions (array of
          { id, labelKey, icon }).

    No processing or validation is performed on inputs.
    """

    def get(self, request):
        return JsonResponse(
            {"status": "success", "data": CONFIG_RESPONSE_DATA},
            status=200,
        )


@method_decorator(csrf_exempt, name="dispatch")
class RecommendView(View):
    """
    POST endpoint for irrigation recommendation.

    Purpose:
        Returns a static irrigation plan (frequencyPerWeek, durationMinutes,
        bestTimeOfDay, moistureLevel, warning). Body may contain crop_id
        and farm info; not read or used in response.

    Input parameters:
        - body (optional): JSON. May contain "crop_id", "soilType", "waterQuality",
          "climateZone". Data type: object. Location: body. Not read or validated;
          not used in response.

    Response structure:
        - status: string, always "success".
        - data: object with key "plan" (object with frequencyPerWeek,
          durationMinutes, bestTimeOfDay, moistureLevel, warning).

    No processing or validation is performed on inputs.
    """

    def post(self, request):
        return JsonResponse(
            {"status": "success", "data": RECOMMEND_RESPONSE_DATA},
            status=200,
        )
