"""
Pest detection API views.
"""

import json

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from config.swagger import status_response
from external_api_adapter import request as external_api_request
from farm_hub.models import FarmHub
from .serializers import (
    PestDetectionAnalyzeRequestSerializer,
    PestDetectionAnalyzeResponseSerializer,
    PestDetectionRiskRequestSerializer,
    PestDetectionRiskResponseSerializer,
    PestDetectionRiskSummaryResponseSerializer,
)


class PestDetectionFarmMixin:
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

    @staticmethod
    def _parse_json_array(value):
        if not isinstance(value, str):
            return None
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError):
            return None
        return parsed if isinstance(parsed, list) else None

    def _collect_uploaded_images(self, request):
        uploaded_images = []
        single_image = request.FILES.get("image")
        if single_image is not None:
            uploaded_images.append(single_image)
        uploaded_images.extend(request.FILES.getlist("images"))
        return uploaded_images

    def _prepare_image_urls(self, request):
        image_urls = request.data.get("image_urls", [])
        if isinstance(image_urls, str):
            parsed = self._parse_json_array(image_urls)
            image_urls = parsed if parsed is not None else [image_urls]
        return [str(item) for item in image_urls if str(item).strip()]

    @staticmethod
    def _attach_uploaded_files(payload, uploaded_images):
        if not uploaded_images:
            return payload

        files = []
        for uploaded_image in uploaded_images:
            files.append(
                (
                    "images",
                    (
                        uploaded_image.name,
                        uploaded_image,
                        getattr(uploaded_image, "content_type", "application/octet-stream"),
                    ),
                )
            )

        multipart_payload = dict(payload)
        multipart_payload["image_urls"] = json.dumps(payload.get("image_urls", []), ensure_ascii=False)
        multipart_payload["__files__"] = files
        return multipart_payload

    @staticmethod
    def _extract_result_payload(adapter_data):
        if not isinstance(adapter_data, dict):
            return {}

        data = adapter_data.get("data")
        if isinstance(data, dict) and isinstance(data.get("result"), dict):
            return data.get("result", {})
        if isinstance(data, dict):
            return data

        result = adapter_data.get("result")
        if isinstance(result, dict):
            return result

        return adapter_data

    @staticmethod
    def _error_response(adapter_response):
        response_data = (
            adapter_response.data
            if isinstance(adapter_response.data, dict)
            else {"message": str(adapter_response.data)}
        )
        return Response(
            {"code": adapter_response.status_code, "msg": "error", "data": response_data},
            status=adapter_response.status_code,
        )


class AnalyzeView(PestDetectionFarmMixin, APIView):
    @extend_schema(
        tags=["Pest Detection"],
        request=PestDetectionAnalyzeRequestSerializer,
        responses={200: status_response("PestDetectionAnalyzeResponse", data=PestDetectionAnalyzeResponseSerializer())},
    )
    def post(self, request):
        serializer = PestDetectionAnalyzeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data.copy()

        farm, error_response = self._get_farm(request, payload.get("farm_uuid"))
        if error_response is not None:
            return error_response

        image_urls = self._prepare_image_urls(request)
        uploaded_images = self._collect_uploaded_images(request)
        if not image_urls and not uploaded_images:
            return Response(
                {
                    "code": 400,
                    "msg": "error",
                    "data": {
                        "images": ["At least one image must be provided via image_urls, image, or images."],
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        ai_payload = {
            "farm_uuid": str(farm.farm_uuid),
            "plant_name": payload.get("plant_name", ""),
            "query": payload.get("query", ""),
            "image_urls": image_urls,
        }
        sensor_uuid = payload.get("sensor_uuid")
        if sensor_uuid:
            ai_payload["sensor_uuid"] = str(sensor_uuid)

        ai_payload = self._attach_uploaded_files(ai_payload, uploaded_images)

        adapter_response = external_api_request(
            "ai",
            "/api/pest-disease/detect/",
            method="POST",
            payload=ai_payload,
        )

        if adapter_response.status_code >= 400:
            return self._error_response(adapter_response)

        return Response(
            {"code": 200, "msg": "success", "data": self._extract_result_payload(adapter_response.data)},
            status=status.HTTP_200_OK,
        )


class RiskView(PestDetectionFarmMixin, APIView):
    @extend_schema(
        tags=["Pest Detection"],
        request=PestDetectionRiskRequestSerializer,
        responses={200: status_response("PestDetectionRiskResponse", data=PestDetectionRiskResponseSerializer())},
    )
    def post(self, request):
        serializer = PestDetectionRiskRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data.copy()

        farm, error_response = self._get_farm(request, payload.get("farm_uuid"))
        if error_response is not None:
            return error_response

        ai_payload = {
            "farm_uuid": str(farm.farm_uuid),
            "plant_name": payload.get("plant_name", ""),
            "growth_stage": payload.get("growth_stage", ""),
            "query": payload.get("query", ""),
        }
        sensor_uuid = payload.get("sensor_uuid")
        if sensor_uuid:
            ai_payload["sensor_uuid"] = str(sensor_uuid)

        adapter_response = external_api_request(
            "ai",
            "/api/pest-disease/risk/",
            method="POST",
            payload=ai_payload,
        )

        if adapter_response.status_code >= 400:
            return self._error_response(adapter_response)

        return Response(
            {"code": 200, "msg": "success", "data": self._extract_result_payload(adapter_response.data)},
            status=status.HTTP_200_OK,
        )


class RiskSummaryView(PestDetectionFarmMixin, APIView):
    @extend_schema(
        tags=["Pest Detection"],
        request=PestDetectionRiskRequestSerializer,
        responses={200: status_response("PestDetectionRiskSummaryResponse", data=PestDetectionRiskSummaryResponseSerializer())},
    )
    def post(self, request):
        farm_uuid = request.data.get("farm_uuid")
        sensor_uuid = request.data.get("sensor_uuid")

        farm, error_response = self._get_farm(request, farm_uuid)
        if error_response is not None:
            return error_response

        payload = {"farm_uuid": str(farm.farm_uuid)}
        if sensor_uuid:
            payload["sensor_uuid"] = str(sensor_uuid)

        adapter_response = external_api_request(
            "ai",
            "/api/pest-disease/risk-summary/",
            method="POST",
            payload=payload,
        )

        if adapter_response.status_code >= 400:
            return self._error_response(adapter_response)

        result = self._extract_result_payload(adapter_response.data)
        response_payload = {
            "farm_uuid": str(farm.farm_uuid),
            "diseaseRisk": result.get("diseaseRisk") or result.get("disease_risk") or {},
            "pestRisk": result.get("pestRisk") or result.get("pest_risk") or {},
            "drivers": result.get("drivers") if isinstance(result.get("drivers"), dict) else {},
        }
        return Response(
            {"code": 200, "msg": "success", "data": response_payload},
            status=status.HTTP_200_OK,
        )
