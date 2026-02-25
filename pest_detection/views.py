"""
Pest Detection API views.
Plain Django only; no DRF. No database. All responses are static mock data.
Response format: {"status": "success", "data": <payload>}. HTTP 200 only.
No processing, validation, or use of input parameters in responses.
CSRF exempt so frontend can call POST without token.
"""

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .mock_data import ANALYZE_RESPONSE_DATA


@method_decorator(csrf_exempt, name="dispatch")
class AnalyzeView(View):
    """
    POST endpoint for pest detection analysis.

    Purpose:
        Returns a static pest detection result (pest name, confidence,
        description, treatment). Used when the user uploads a plant image
        and requests analysis. No processing is performed on the request.

    Input parameters:
        - body (optional): JSON or form-data; may contain image or file.
          Data type: object. Location: body. Not read or validated; not used in response.

    Response structure:
        - status: string, always "success".
        - data: object with keys pest (string), confidence (number),
          description (string), treatment (string).

    No processing or validation is performed on inputs.
    """

    def post(self, request):
        return JsonResponse(
            {"status": "success", "data": ANALYZE_RESPONSE_DATA},
            status=200,
        )
