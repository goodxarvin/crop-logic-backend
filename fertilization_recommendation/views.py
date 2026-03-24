"""
Fertilization Recommendation API views.
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
from external_api_adapter import request as external_api_request
from .mock_data import CONFIG_RESPONSE_DATA


class ConfigView(APIView):
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

    @extend_schema(
        tags=["Fertilization Recommendation"],
        responses={200: status_response("FertilizationConfigResponse", data=serializers.JSONField())},
    )
    def get(self, request):
        return Response(
            {"status": "success", "data": CONFIG_RESPONSE_DATA},
            status=status.HTTP_200_OK,
        )


class RecommendView(APIView):
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

    @extend_schema(
        tags=["Fertilization Recommendation"],
        request=OpenApiTypes.OBJECT,
        responses={200: status_response("FertilizationRecommendResponse", data=serializers.JSONField())},
    )
    def post(self, request):
        adapter_response = external_api_request(
            "ai",
            "/fertilization/recommend",
            method="POST",
            payload=request.data,
        )
        return Response(adapter_response.data, status=adapter_response.status_code)
