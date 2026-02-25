"""
Fertilization Recommendation API views.
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
    GET endpoint for fertilization config (farm data, growth stages, crop options).

    Purpose:
        Returns static farm data (soilType, organicMatter, waterEC), growth
        stages list, and crop options for the fertilization recommendation form.
        Used when loading the fertilization recommendation page.

    Input parameters:
        None. Query parameters, if sent, are not read or used.

    Response structure:
        - status: string, always "success".
        - data: object with keys farmData (object), growthStages (array of
          { id, icon }), cropOptions (array of { id, labelKey, icon }).

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
    POST endpoint for fertilization recommendation.

    Purpose:
        Returns a static fertilization plan (npkRatio, amountPerHectare,
        applicationMethod, applicationInterval, reasoning). Body may contain
        crop_id, growth_stage, farm_data; not read or used in response.

    Input parameters:
        - body (optional): JSON. May contain "crop_id", "growth_stage",
          "soilType", "organicMatter", "waterEC". Data type: object.
          Location: body. Not read or validated; not used in response.

    Response structure:
        - status: string, always "success".
        - data: object with key "plan" (object with npkRatio, amountPerHectare,
          applicationMethod, applicationInterval, reasoning).

    No processing or validation is performed on inputs.
    """

    def post(self, request):
        return JsonResponse(
            {"status": "success", "data": RECOMMEND_RESPONSE_DATA},
            status=200,
        )
