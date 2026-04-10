"""
Fertilization Recommendation API views.
"""

from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from config.swagger import status_response
from external_api_adapter import request as external_api_request
from farm_hub.models import FarmHub
from .mock_data import CONFIG_RESPONSE_DATA
from .models import FertilizationRecommendationRequest
from .serializers import (
    FertilizationRecommendRequestSerializer,
    FertilizationRecommendResponseDataSerializer,
    FertilizationTaskStatusDataSerializer,
    FertilizationTaskSubmitDataSerializer,
)


class FarmAccessMixin:
    @staticmethod
    def _get_farm(request, farm_uuid):
        if not farm_uuid:
            raise serializers.ValidationError({"farm_uuid": ["This field is required."]})
        try:
            return FarmHub.objects.get(farm_uuid=farm_uuid, owner=request.user)
        except FarmHub.DoesNotExist as exc:
            raise serializers.ValidationError({"farm_uuid": ["Farm not found."]}) from exc


class ConfigView(FarmAccessMixin, APIView):
    @extend_schema(
        tags=["Fertilization Recommendation"],
        parameters=[
            OpenApiParameter(name="farm_uuid", type=OpenApiTypes.UUID, location=OpenApiParameter.QUERY, required=True, default="11111111-1111-1111-1111-111111111111"),
        ],
        responses={200: status_response("FertilizationConfigResponse", data=serializers.JSONField())},
    )
    def get(self, request):
        farm = self._get_farm(request, request.query_params.get("farm_uuid"))
        data = dict(CONFIG_RESPONSE_DATA)
        data["farm_uuid"] = str(farm.farm_uuid)
        return Response({"status": "success", "data": data}, status=status.HTTP_200_OK)


class RecommendView(FarmAccessMixin, APIView):
    @extend_schema(
        tags=["Fertilization Recommendation"],
        request=FertilizationRecommendRequestSerializer,
        responses={200: status_response("FertilizationRecommendResponse", data=FertilizationRecommendResponseDataSerializer())},
    )
    def post(self, request):
        serializer = FertilizationRecommendRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data.copy()
        farm = self._get_farm(request, payload.get("farm_uuid"))
        payload["farm_uuid"] = str(farm.farm_uuid)

        adapter_response = external_api_request(
            "ai",
            "/fertilization/recommend",
            method="POST",
            payload=payload,
        )

        response_data = adapter_response.data if isinstance(adapter_response.data, dict) else {}
        FertilizationRecommendationRequest.objects.create(
            farm=farm,
            crop_id=payload.get("crop_id", ""),
            growth_stage=payload.get("growth_stage", ""),
            task_id=str(response_data.get("data", {}).get("task_id") or response_data.get("task_id") or ""),
            status=str(response_data.get("data", {}).get("status") or response_data.get("status") or ""),
            request_payload=payload,
            response_payload=adapter_response.data if isinstance(adapter_response.data, dict) else {"raw": adapter_response.data},
        )
        return Response(adapter_response.data, status=adapter_response.status_code)


class RecommendTaskStatusView(FarmAccessMixin, APIView):
    @extend_schema(
        tags=["Fertilization Recommendation"],
        parameters=[
            OpenApiParameter(name="task_id", type=OpenApiTypes.STR, location=OpenApiParameter.PATH),
            OpenApiParameter(name="farm_uuid", type=OpenApiTypes.UUID, location=OpenApiParameter.QUERY, required=True, default="11111111-1111-1111-1111-111111111111"),
        ],
        responses={200: status_response("FertilizationRecommendTaskStatusResponse", data=FertilizationTaskStatusDataSerializer())},
    )
    def get(self, request, task_id):
        farm = self._get_farm(request, request.query_params.get("farm_uuid"))
        adapter_response = external_api_request(
            "ai",
            f"/fertilization/status/{task_id}",
            method="GET",
            query={"farm_uuid": str(farm.farm_uuid)},
        )
        response_data = adapter_response.data if isinstance(adapter_response.data, dict) else {}
        FertilizationRecommendationRequest.objects.filter(farm=farm, task_id=task_id).update(
            status=str(response_data.get("data", {}).get("status") or response_data.get("status") or ""),
            response_payload=adapter_response.data if isinstance(adapter_response.data, dict) else {"raw": adapter_response.data},
        )
        return Response(adapter_response.data, status=adapter_response.status_code)
