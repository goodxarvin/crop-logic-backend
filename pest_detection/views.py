"""
Pest Detection API views.
No database. All responses are static mock data.
Response format: {"status": "success", "data": <payload>}. HTTP 200 only.
No processing, validation, or use of input parameters in responses.
"""

from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema

from config.swagger import status_response
from .mock_data import ANALYZE_RESPONSE_DATA


class AnalyzeView(APIView):
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

    @extend_schema(
        tags=["Pest Detection"],
        request=OpenApiTypes.OBJECT,
        responses={200: status_response("PestDetectionAnalyzeResponse", data=serializers.JSONField())},
    )
    def post(self, request):
        return Response(
            {"status": "success", "data": ANALYZE_RESPONSE_DATA},
            status=status.HTTP_200_OK,
        )
