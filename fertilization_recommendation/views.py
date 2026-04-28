"""
Fertilization Recommendation API views.
"""

import logging

from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from config.swagger import code_response, status_response
from external_api_adapter import request as external_api_request
from farm_hub.models import FarmHub
from .mock_data import CONFIG_RESPONSE_DATA
from .models import FertilizationRecommendationRequest
from .serializers import (
    FertilizationRecommendRequestSerializer,
    FertilizationRecommendResponseDataSerializer,
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
        tags=["Fertilization Recommendation"],
        responses={200: status_response("FertilizationConfigResponse", data=serializers.JSONField())},
    )
    def get(self, request):
        farm = self._get_farm(request, request.query_params.get("farm_uuid"))
        data = dict(CONFIG_RESPONSE_DATA)
        data["farm_uuid"] = str(farm.farm_uuid)
        return Response({"status": "success", "data": data}, status=status.HTTP_200_OK)


class RecommendView(FarmAccessMixin, APIView):
    @staticmethod
    def _to_string(value):
        if value is None:
            return ""
        return str(value)

    @staticmethod
    def _to_float(value):
        if value in (None, ""):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_int(value):
        if value in (None, ""):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

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
            "fertilizerType",
            "amount",
            "applicationMethod",
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

    @staticmethod
    def _extract_public_payload(adapter_data):
        if not isinstance(adapter_data, dict):
            return {}

        data = adapter_data.get("data")
        if isinstance(data, dict):
            result = data.get("result")
            if isinstance(result, dict):
                return result
            return data

        result = adapter_data.get("result")
        if isinstance(result, dict):
            return result

        return adapter_data

    def _normalize_npk_ratio(self, raw_ratio):
        if not isinstance(raw_ratio, dict):
            return {}

        normalized = {}
        for key in ("n", "p", "k"):
            numeric_value = self._to_float(raw_ratio.get(key))
            if numeric_value is not None:
                normalized[key] = numeric_value

        label = self._to_string(raw_ratio.get("label")).strip()
        if label:
            normalized["label"] = label

        return normalized

    def _normalize_named_object(self, raw_object):
        if not isinstance(raw_object, dict):
            return {}

        normalized = {}
        for key in ("id", "label", "unit", "calculation_basis"):
            value = self._to_string(raw_object.get(key)).strip()
            if value:
                normalized[key] = value

        for key in ("value", "base_amount_per_hectare", "base_amount_per_square_meter"):
            numeric_value = self._to_float(raw_object.get(key))
            if numeric_value is not None:
                normalized[key] = numeric_value

        return normalized

    def _normalize_primary_recommendation(self, payload):
        raw_data = payload.get("primary_recommendation")
        if not isinstance(raw_data, dict):
            return {}

        normalized = {}
        for key in (
            "fertilizer_code",
            "fertilizer_name",
            "display_title",
            "fertilizer_type",
            "reasoning",
            "summary",
        ):
            value = self._to_string(raw_data.get(key)).strip()
            if value:
                normalized[key] = value

        npk_ratio = self._normalize_npk_ratio(raw_data.get("npk_ratio"))
        if npk_ratio:
            normalized["npk_ratio"] = npk_ratio

        application_method = self._normalize_named_object(raw_data.get("application_method"))
        if application_method:
            normalized["application_method"] = {
                key: value for key, value in application_method.items() if key in {"id", "label"}
            }

        application_interval = self._normalize_named_object(raw_data.get("application_interval"))
        if application_interval:
            normalized["application_interval"] = {
                key: value for key, value in application_interval.items() if key in {"value", "unit", "label"}
            }

        dosage = self._normalize_named_object(raw_data.get("dosage"))
        if dosage:
            dosage_label = self._to_string(raw_data.get("dosage", {}).get("label")).strip()
            if dosage_label:
                dosage["label"] = dosage_label
            normalized["dosage"] = {
                key: value
                for key, value in dosage.items()
                if key in {"base_amount_per_hectare", "base_amount_per_square_meter", "unit", "label", "calculation_basis"}
            }

        return normalized

    def _normalize_nutrient_items(self, items):
        if not isinstance(items, list):
            return []

        normalized_items = []
        for item in items:
            if not isinstance(item, dict):
                continue
            normalized_item = {}
            for key in ("key", "name", "unit", "description"):
                value = self._to_string(item.get(key)).strip()
                if value:
                    normalized_item[key] = value
            numeric_value = self._to_float(item.get("value"))
            if numeric_value is not None:
                normalized_item["value"] = numeric_value
            if normalized_item:
                normalized_items.append(normalized_item)
        return normalized_items

    def _normalize_application_guide(self, payload):
        raw_data = payload.get("application_guide")
        if not isinstance(raw_data, dict):
            return {}

        normalized = {}
        safety_warning = self._to_string(raw_data.get("safety_warning")).strip()
        if safety_warning:
            normalized["safety_warning"] = safety_warning

        raw_steps = raw_data.get("steps")
        if isinstance(raw_steps, list):
            steps = []
            for step in raw_steps:
                if not isinstance(step, dict):
                    continue
                normalized_step = {}
                step_number = self._to_int(step.get("step_number"))
                if step_number is not None:
                    normalized_step["step_number"] = step_number
                for key in ("title", "description"):
                    value = self._to_string(step.get(key)).strip()
                    if value:
                        normalized_step[key] = value
                if normalized_step:
                    steps.append(normalized_step)
            normalized["steps"] = steps

        return normalized

    def _normalize_alternatives(self, payload):
        raw_items = payload.get("alternative_recommendations")
        if not isinstance(raw_items, list):
            return []

        alternatives = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            normalized_item = {}
            for key in ("fertilizer_code", "fertilizer_name", "fertilizer_type", "usage_method", "description"):
                value = self._to_string(item.get(key)).strip()
                if value:
                    normalized_item[key] = value
            if normalized_item:
                alternatives.append(normalized_item)
        return alternatives

    def _normalize_response_payload(self, adapter_data):
        payload = self._extract_public_payload(adapter_data)
        if not isinstance(payload, dict):
            payload = {}

        normalized_sections = self._normalize_sections(payload.get("sections"))
        nutrient_analysis = payload.get("nutrient_analysis") if isinstance(payload.get("nutrient_analysis"), dict) else {}

        return {
            "primary_recommendation": self._normalize_primary_recommendation(payload),
            "nutrient_analysis": {
                "macro": self._normalize_nutrient_items(nutrient_analysis.get("macro")),
                "micro": self._normalize_nutrient_items(nutrient_analysis.get("micro")),
            },
            "application_guide": self._normalize_application_guide(payload),
            "alternative_recommendations": self._normalize_alternatives(payload),
            "sections": normalized_sections,
        }

    @extend_schema(
        tags=["Fertilization Recommendation"],
        request=FertilizationRecommendRequestSerializer,
        responses={200: code_response("FertilizationRecommendResponse", data=FertilizationRecommendResponseDataSerializer())},
    )
    def post(self, request):
        serializer = FertilizationRecommendRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data.copy()
        farm = self._get_farm(request, payload.get("farm_uuid"))
        payload["farm_uuid"] = str(farm.farm_uuid)
        payload["plant_name"] = payload.get("plant_name", "")
        payload["growth_stage"] = payload.get("growth_stage", "")

        adapter_response = external_api_request(
            "ai",
            "/api/fertilization/recommend/",
            method="POST",
            payload=payload,
        )

        response_data = adapter_response.data if isinstance(adapter_response.data, dict) else {}
        public_data = self._normalize_response_payload(response_data)

        logger.warning(
            "Fertilization recommendation response parsed: farm_uuid=%s status_code=%s response_keys=%s sections_count=%s",
            str(farm.farm_uuid),
            adapter_response.status_code,
            sorted(response_data.keys()) if isinstance(response_data, dict) else None,
            len(public_data.get("sections", [])),
        )

        FertilizationRecommendationRequest.objects.create(
            farm=farm,
            crop_id=payload.get("plant_name", ""),
            growth_stage=payload.get("growth_stage", ""),
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
                "data": public_data,
            },
            status=status.HTTP_200_OK,
        )
