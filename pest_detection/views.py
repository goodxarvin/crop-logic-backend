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
from drf_spectacular.utils import OpenApiParameter, extend_schema

from config.swagger import status_response
from external_api_adapter import request as external_api_request
from .mock_data import ANALYZE_RESPONSE_DATA
from .serializers import RiskSummaryDataSerializer


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


class RiskSummaryView(APIView):
    """
    GET endpoint for combined pest and disease risk summary.

    Purpose:
        Returns disease_risk and pest_risk card data for the farm dashboard.
        Calls the AI external adapter for live/mock risk assessment results.

    Input parameters:
        - farm_uuid (query, optional): UUID of the farm to assess.

    Response structure:
        - status: string, always "success".
        - data: object with keys disease_risk and pest_risk,
          each containing card display fields (id, title, subtitle, stats,
          avatarColor, avatarIcon, chipText, chipColor) and a details object.
    """

    @extend_schema(
        tags=["Pest Detection"],
        parameters=[
            OpenApiParameter(
                name="farm_uuid",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                required=False,
                description="UUID of the farm for risk assessment.",
                default="11111111-1111-1111-1111-111111111111"),
        ],
        responses={200: status_response("PestDetectionRiskSummaryResponse", data=RiskSummaryDataSerializer())},
    )
    def get(self, request):
        farm_uuid = request.query_params.get("farm_uuid")
        query = {"farm_uuid": str(farm_uuid)} if farm_uuid else {}

        adapter_response = external_api_request(
            "ai",
            "/pest-detection/risk-summary",
            method="GET",
            query=query,
        )

        response_data = adapter_response.data if isinstance(adapter_response.data, dict) else {}
        result = response_data.get("result", response_data.get("data", response_data))

        return Response(
            {"status": "success", "data": result},
            status=status.HTTP_200_OK,
        )
