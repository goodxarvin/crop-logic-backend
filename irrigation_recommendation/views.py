"""
Irrigation Recommendation API views.
"""

import logging

from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from config.swagger import status_response
from external_api_adapter import request as external_api_request
from farm_hub.models import FarmHub
from water.serializers import WaterStressIndexSerializer
from water.views import WaterStressIndexView
from .mock_data import CONFIG_RESPONSE_DATA
from .models import IrrigationRecommendationRequest
from .serializers import (
    IrrigationMethodSerializer,
    IrrigationRecommendRequestSerializer,
    IrrigationRecommendResponseDataSerializer,
    WaterStressRequestSerializer,
)


logger = logging.getLogger(__name__)


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
        tags=["Irrigation Recommendation"],
        responses={200: status_response("IrrigationConfigResponse", data=serializers.JSONField())},
    )
    def get(self, request):
        farm = self._get_farm(request, request.query_params.get("farm_uuid"))
        data = dict(CONFIG_RESPONSE_DATA)
        data["farm_uuid"] = str(farm.farm_uuid)
        return Response({"status": "success", "data": data}, status=status.HTTP_200_OK)


class IrrigationMethodListView(APIView):
    @staticmethod
    def _extract_methods(adapter_data):
        if not isinstance(adapter_data, dict):
            return adapter_data if isinstance(adapter_data, list) else []

        data = adapter_data.get("data")
        if isinstance(data, dict) and isinstance(data.get("result"), list):
            return data["result"]
        if isinstance(data, list):
            return data

        result = adapter_data.get("result")
        if isinstance(result, list):
            return result

        return []

    @extend_schema(
        tags=["Irrigation Recommendation"],
        responses={200: status_response("IrrigationMethodListResponse", data=IrrigationMethodSerializer(many=True))},
    )
    def get(self, request):
        adapter_response = external_api_request(
            "ai",
            "/api/irrigation/",
            method="GET",
        )

        if adapter_response.status_code >= 400:
            response_data = adapter_response.data if isinstance(adapter_response.data, dict) else {"message": str(adapter_response.data)}
            return Response(
                {"code": adapter_response.status_code, "msg": "error", "data": response_data},
                status=adapter_response.status_code,
            )

        return Response(
            {"code": 200, "msg": "success", "data": self._extract_methods(adapter_response.data)},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Irrigation Recommendation"],
        request=serializers.JSONField,
        responses={201: status_response("IrrigationMethodCreateResponse", data=IrrigationMethodSerializer())},
    )
    def post(self, request):
        adapter_response = external_api_request(
            "ai",
            "/api/irrigation/",
            method="POST",
            payload=request.data,
        )

        response_data = adapter_response.data if isinstance(adapter_response.data, dict) else {"message": str(adapter_response.data)}
        if adapter_response.status_code >= 400:
            return Response(
                {"code": adapter_response.status_code, "msg": "error", "data": response_data},
                status=adapter_response.status_code,
            )

        payload = self._extract_methods(adapter_response.data)
        if not payload:
            payload = response_data.get("data", response_data)

        return Response(
            {"code": adapter_response.status_code, "msg": "success", "data": payload},
            status=adapter_response.status_code,
        )


class RecommendView(FarmAccessMixin, APIView):
    @staticmethod
    def _normalize_sections(raw_sections):
        if not isinstance(raw_sections, list):
            return []

        allowed_keys = {
            "type",
            "title",
            "icon",
            "content",
            "items",
            "frequency",
            "amount",
            "timing",
            "validityPeriod",
            "expandableExplanation",
        }

        normalized_sections = []
        for section in raw_sections:
            if not isinstance(section, dict) or not section.get("type"):
                continue

            normalized_section = {}
            for key in allowed_keys:
                value = section.get(key)
                if value is None:
                    continue
                if key == "items":
                    if not isinstance(value, list):
                        continue
                    normalized_section[key] = [str(item) for item in value]
                    continue
                normalized_section[key] = str(value) if key != "type" else value

            normalized_sections.append(normalized_section)
        return normalized_sections

    def _extract_public_sections(self, adapter_data):
        if not isinstance(adapter_data, dict):
            return []

        data = adapter_data.get("data")
        if isinstance(data, dict) and isinstance(data.get("sections"), list):
            return self._normalize_sections(data.get("sections"))

        result = data.get("result") if isinstance(data, dict) else None
        if isinstance(result, dict) and isinstance(result.get("sections"), list):
            return self._normalize_sections(result.get("sections"))

        if isinstance(adapter_data.get("sections"), list):
            return self._normalize_sections(adapter_data.get("sections"))

        return []

    @extend_schema(
        tags=["Irrigation Recommendation"],
        request=IrrigationRecommendRequestSerializer,
        responses={200: status_response("IrrigationRecommendResponse", data=IrrigationRecommendResponseDataSerializer())},
    )
    def post(self, request):
        serializer = IrrigationRecommendRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data.copy()
        farm = self._get_farm(request, payload.get("farm_uuid"))
        payload["farm_uuid"] = str(farm.farm_uuid)

        adapter_response = external_api_request(
            "ai",
            "/api/irrigation/recommend/",
            method="POST",
            payload=payload,
        )

        response_data = adapter_response.data if isinstance(adapter_response.data, dict) else {}
        public_sections = self._extract_public_sections(response_data)

        logger.warning(
            "Irrigation recommendation response parsed: farm_uuid=%s status_code=%s response_keys=%s sections_count=%s",
            str(farm.farm_uuid),
            adapter_response.status_code,
            sorted(response_data.keys()) if isinstance(response_data, dict) else None,
            len(public_sections),
        )

        IrrigationRecommendationRequest.objects.create(
            farm=farm,
            crop_id=payload.get("plant_name", ""),
            task_id="",
            status="success" if adapter_response.status_code < 400 else "error",
            request_payload=payload,
            response_payload=adapter_response.data if isinstance(adapter_response.data, dict) else {"raw": adapter_response.data},
        )
        if adapter_response.status_code >= 400:
            return Response(
                {
                    "code": adapter_response.status_code,
                    "msg": "error",
                    "data": response_data if isinstance(response_data, dict) else {"message": str(adapter_response.data)},
                },
                status=adapter_response.status_code,
            )

        return Response(
            {
                "code": 200,
                "msg": "success",
                "data": {
                    "sections": public_sections,
                },
            },
            status=status.HTTP_200_OK,
        )


class WaterStressView(APIView):
    @staticmethod
    def _get_farm(request, farm_uuid):
        if not farm_uuid:
            return None, Response(
                {"code": 400, "msg": "error", "data": {"farm_uuid": ["This field is required."]}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            return FarmHub.objects.get(farm_uuid=farm_uuid, owner=request.user), None
        except FarmHub.DoesNotExist:
            return None, Response(
                {"code": 404, "msg": "error", "data": {"farm_uuid": ["Farm not found."]}},
                status=status.HTTP_404_NOT_FOUND,
            )

    @extend_schema(
        tags=["Irrigation Recommendation"],
        request=WaterStressRequestSerializer,
        responses={200: status_response("WaterStressResponse", data=WaterStressIndexSerializer())},
    )
    def post(self, request):
        serializer = WaterStressRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data.copy()

        farm, error_response = self._get_farm(request, payload.get("farm_uuid"))
        if error_response is not None:
            return error_response

        query = {"farm_uuid": str(farm.farm_uuid)}
        sensor_uuid = payload.get("sensor_uuid")
        if sensor_uuid:
            query["sensor_uuid"] = str(sensor_uuid)

        adapter_response = external_api_request(
            "ai",
            "/api/irrigation/water-stress/",
            method="POST",
            payload=query,
        )

        if adapter_response.status_code >= 400:
            response_data = adapter_response.data if isinstance(adapter_response.data, dict) else {"message": str(adapter_response.data)}
            return Response(
                {"code": adapter_response.status_code, "msg": "error", "data": response_data},
                status=adapter_response.status_code,
            )

        stress_payload = WaterStressIndexView.extract_stress_payload(adapter_response.data, farm.farm_uuid)
        return Response(
            {"code": 200, "msg": "success", "data": stress_payload},
            status=status.HTTP_200_OK,
        )
