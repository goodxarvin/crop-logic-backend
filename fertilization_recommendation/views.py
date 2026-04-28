"""
Fertilization Recommendation API views.
"""

import logging

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from rest_framework import serializers, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from config.swagger import code_response, status_response
from external_api_adapter import request as external_api_request
from farm_hub.models import FarmHub
from .mock_data import CONFIG_RESPONSE_DATA
from .models import FertilizationRecommendationRequest
from .serializers import (
    FertilizationRecommendationListItemSerializer,
    FertilizationRecommendationListQuerySerializer,
    FertilizationRecommendRequestSerializer,
    FertilizationRecommendResponseDataSerializer,
)


logger = logging.getLogger(__name__)


class FertilizationRecommendationPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        page_size = self.get_page_size(self.request) or self.page.paginator.per_page
        return Response(
            {
                "code": 200,
                "msg": "success",
                "data": data,
                "pagination": {
                    "page": self.page.number,
                    "page_size": page_size,
                    "total_pages": self.page.paginator.num_pages,
                    "total_items": self.page.paginator.count,
                    "has_next": self.page.has_next(),
                    "has_previous": self.page.has_previous(),
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                },
            },
            status=status.HTTP_200_OK,
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

    @staticmethod
    def _first_non_empty(*values):
        for value in values:
            if value is None:
                continue
            text = str(value).strip()
            if text:
                return text
        return ""

    def _normalize_primary_recommendation(self, payload):
        raw_data = payload.get("primary_recommendation")
        if not isinstance(raw_data, dict):
            raw_data = {}

        normalized = {}
        scalar_fields = {
            "fertilizer_code": (
                raw_data.get("fertilizer_code"),
                payload.get("fertilizer_code"),
            ),
            "fertilizer_name": (
                raw_data.get("fertilizer_name"),
                payload.get("fertilizer_name"),
            ),
            "display_title": (
                raw_data.get("display_title"),
                payload.get("display_title"),
            ),
            "fertilizer_type": (
                raw_data.get("fertilizer_type"),
                payload.get("fertilizer_type"),
            ),
            "reasoning": (
                raw_data.get("reasoning"),
                payload.get("reasoning"),
            ),
            "summary": (
                raw_data.get("summary"),
                payload.get("summary"),
            ),
        }
        for key, values in scalar_fields.items():
            value = self._first_non_empty(*values)
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
        crop_id = self._first_non_empty(payload.get("crop_id"), payload.get("plant_name"))
        plant_name = self._first_non_empty(payload.get("plant_name"), payload.get("crop_id"))
        payload["farm_uuid"] = str(farm.farm_uuid)
        payload["crop_id"] = crop_id
        payload["plant_name"] = plant_name
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
            crop_id=crop_id,
            growth_stage=payload.get("growth_stage", ""),
            task_id="",
            status=FertilizationRecommendationRequest.STATUS_PENDING_CONFIRMATION,
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


class RecommendationListView(FarmAccessMixin, APIView):
    permission_classes = RecommendView.permission_classes
    pagination_class = FertilizationRecommendationPagination

    @extend_schema(
        tags=["Fertilization Recommendation"],
        parameters=[FertilizationRecommendationListQuerySerializer],
        responses={200: code_response("FertilizationRecommendationListResponse")},
    )
    def get(self, request):
        serializer = FertilizationRecommendationListQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        farm = self._get_farm(request, serializer.validated_data["farm_uuid"])
        recommendations = farm.fertilization_recommendations.all().order_by("-created_at", "-id")

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(recommendations, request, view=self)

        items = []
        view_helper = RecommendView()
        for recommendation in page:
            normalized_payload = view_helper._normalize_response_payload(recommendation.response_payload)
            recommendation.fertilizer_type = (
                normalized_payload.get("primary_recommendation", {}).get("fertilizer_type", "")
            )
            items.append(recommendation)

        data = FertilizationRecommendationListItemSerializer(items, many=True).data
        return paginator.get_paginated_response(data)


class RecommendationDetailView(FarmAccessMixin, APIView):
    @extend_schema(
        tags=["Fertilization Recommendation"],
        parameters=[
            OpenApiParameter(
                name="recommendation_uuid",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                required=True,
            )
        ],
        responses={
            200: code_response("FertilizationRecommendationDetailResponse", data=FertilizationRecommendResponseDataSerializer()),
            404: code_response("FertilizationRecommendationDetailNotFoundResponse"),
        },
    )
    def get(self, request, recommendation_uuid):
        recommendation = FertilizationRecommendationRequest.objects.filter(
            uuid=recommendation_uuid,
            farm__owner=request.user,
        ).select_related("farm").first()
        if recommendation is None:
            return Response({"code": 404, "msg": "Recommendation not found."}, status=status.HTTP_404_NOT_FOUND)

        view_helper = RecommendView()
        data = view_helper._normalize_response_payload(recommendation.response_payload)
        data["recommendation_uuid"] = str(recommendation.uuid)
        data["crop_id"] = recommendation.crop_id
        data["plant_name"] = recommendation.crop_id
        data["growth_stage"] = recommendation.growth_stage
        data["status"] = recommendation.status
        data["status_label"] = recommendation.get_status_display()
        return Response({"code": 200, "msg": "success", "data": data}, status=status.HTTP_200_OK)
