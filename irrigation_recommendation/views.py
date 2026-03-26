"""
Irrigation Recommendation API views.
"""

from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from config.swagger import status_response
from external_api_adapter import request as external_api_request
from .mock_data import CONFIG_RESPONSE_DATA
from .serializers import (
    IrrigationRecommendRequestSerializer,
    IrrigationRecommendResponseDataSerializer,
    IrrigationTaskStatusDataSerializer,
    IrrigationTaskSubmitDataSerializer,
)


class ConfigView(APIView):
    @extend_schema(
        tags=["Irrigation Recommendation"],
        responses={200: status_response("IrrigationConfigResponse", data=serializers.JSONField())},
    )
    def get(self, request):
        return Response({"status": "success", "data": CONFIG_RESPONSE_DATA}, status=status.HTTP_200_OK)


class RecommendView(APIView):
    @extend_schema(
        tags=["Irrigation Recommendation"],
        request=IrrigationRecommendRequestSerializer,
        responses={200: status_response("IrrigationRecommendResponse", data=IrrigationRecommendResponseDataSerializer())},
    )
    def post(self, request):
        adapter_response = external_api_request(
            "ai",
            "/irrigation/recommend",
            method="POST",
            payload=request.data,
        )
        return Response(adapter_response.data, status=adapter_response.status_code)


class RecommendTaskCreateView(APIView):
    @extend_schema(
        tags=["Irrigation Recommendation"],
        request=IrrigationRecommendRequestSerializer,
        responses={200: status_response("IrrigationRecommendTaskCreateResponse", data=IrrigationTaskSubmitDataSerializer())},
    )
    def post(self, request):
        adapter_response = external_api_request(
            "ai",
            "/irrigation/recommend",
            method="POST",
            payload=request.data,
        )
        return Response(adapter_response.data, status=adapter_response.status_code)


class RecommendTaskStatusView(APIView):
    @extend_schema(
        tags=["Irrigation Recommendation"],
        parameters=[
            OpenApiParameter(name="task_id", type=OpenApiTypes.STR, location=OpenApiParameter.PATH),
        ],
        responses={200: status_response("IrrigationRecommendTaskStatusResponse", data=IrrigationTaskStatusDataSerializer())},
    )
    def get(self, request, task_id):
        adapter_response = external_api_request(
            "ai",
            f"/irrigation/recommend/status/{task_id}",
            method="GET",
        )
        return Response(adapter_response.data, status=adapter_response.status_code)
