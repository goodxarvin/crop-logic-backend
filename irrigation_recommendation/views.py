"""
Irrigation Recommendation API views.
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
from water.serializers import WaterStressIndexSerializer
from water.views import WaterStressIndexView
from .mock_data import CONFIG_RESPONSE_DATA
from .models import IrrigationRecommendationRequest
from .serializers import (
    FreeTextPlanParserRequestSerializer,
    FreeTextPlanParserResponseDataSerializer,
    IrrigationMethodSerializer,
    IrrigationRecommendationListItemSerializer,
    IrrigationRecommendationListQuerySerializer,
    IrrigationRecommendRequestSerializer,
    IrrigationRecommendResponseDataSerializer,
    WaterStressRequestSerializer,
)
from .services import build_recommendation_response


logger = logging.getLogger(__name__)


class IrrigationRecommendationPagination(PageNumberPagination):
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
        payload.pop("sensor_uuid", None)
        payload.pop("irrigation_type", None)
        payload.pop("irrigation_method_name", None)

        if farm.irrigation_method_name:
            payload["irrigation_method_name"] = farm.irrigation_method_name
            payload["irrigation_type"] = farm.irrigation_method_name
        if farm.irrigation_method_id is not None:
            payload["irrigation_method_id"] = farm.irrigation_method_id

        adapter_response = external_api_request(
            "ai",
            "/api/irrigation/recommend/",
            method="POST",
            payload=payload,
        )

        response_data = adapter_response.data if isinstance(adapter_response.data, dict) else {}
        recommendation_data = build_recommendation_response(response_data)

        logger.warning(
            "Irrigation recommendation response parsed: farm_uuid=%s status_code=%s response_keys=%s sections_count=%s",
            str(farm.farm_uuid),
            adapter_response.status_code,
            sorted(response_data.keys()) if isinstance(response_data, dict) else None,
            len(recommendation_data["sections"]),
        )

        recommendation = IrrigationRecommendationRequest.objects.create(
            farm=farm,
            crop_id=payload.get("plant_name", ""),
            growth_stage=payload.get("growth_stage", ""),
            task_id="",
            status=(
                IrrigationRecommendationRequest.STATUS_PENDING_CONFIRMATION
                if adapter_response.status_code < 400
                else IrrigationRecommendationRequest.STATUS_ERROR
            ),
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

        recommendation_data["recommendation_uuid"] = str(recommendation.uuid)
        recommendation_data["crop_id"] = recommendation.crop_id
        recommendation_data["plant_name"] = recommendation.crop_id
        recommendation_data["growth_stage"] = recommendation.growth_stage
        recommendation_data["irrigation_method_name"] = payload.get("irrigation_method_name", "")
        recommendation_data["status"] = recommendation.status
        recommendation_data["status_label"] = recommendation.get_status_display()

        return Response(
            {
                "code": 200,
                "msg": "success",
                "data": recommendation_data,
            },
            status=status.HTTP_200_OK,
        )


class RecommendationListView(FarmAccessMixin, APIView):
    pagination_class = IrrigationRecommendationPagination

    @extend_schema(
        tags=["Irrigation Recommendation"],
        parameters=[IrrigationRecommendationListQuerySerializer],
        responses={200: code_response("IrrigationRecommendationListResponse")},
    )
    def get(self, request):
        serializer = IrrigationRecommendationListQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        farm = self._get_farm(request, serializer.validated_data["farm_uuid"])
        recommendations = farm.irrigation_recommendations.all().order_by("-created_at", "-id")

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(recommendations, request, view=self)

        items = []
        for recommendation in page:
            request_payload = recommendation.request_payload if isinstance(recommendation.request_payload, dict) else {}
            recommendation.irrigation_method_name = str(request_payload.get("irrigation_method_name") or "")
            items.append(recommendation)

        data = IrrigationRecommendationListItemSerializer(items, many=True).data
        return paginator.get_paginated_response(data)


class RecommendationDetailView(FarmAccessMixin, APIView):
    @extend_schema(
        tags=["Irrigation Recommendation"],
        parameters=[
            OpenApiParameter(
                name="recommendation_uuid",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                required=True,
            )
        ],
        responses={
            200: code_response("IrrigationRecommendationDetailResponse", data=IrrigationRecommendResponseDataSerializer()),
            404: code_response("IrrigationRecommendationDetailNotFoundResponse"),
        },
    )
    def get(self, request, recommendation_uuid):
        recommendation = IrrigationRecommendationRequest.objects.filter(
            uuid=recommendation_uuid,
            farm__owner=request.user,
        ).select_related("farm").first()
        if recommendation is None:
            return Response({"code": 404, "msg": "Recommendation not found."}, status=status.HTTP_404_NOT_FOUND)

        data = build_recommendation_response(recommendation.response_payload)
        request_payload = recommendation.request_payload if isinstance(recommendation.request_payload, dict) else {}
        data["recommendation_uuid"] = str(recommendation.uuid)
        data["crop_id"] = recommendation.crop_id
        data["plant_name"] = recommendation.crop_id
        data["growth_stage"] = recommendation.growth_stage
        data["irrigation_method_name"] = str(request_payload.get("irrigation_method_name") or "")
        data["status"] = recommendation.status
        data["status_label"] = recommendation.get_status_display()
        return Response({"code": 200, "msg": "success", "data": data}, status=status.HTTP_200_OK)


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


class PlanFromTextView(FarmAccessMixin, APIView):
    @extend_schema(
        tags=["Irrigation Recommendation"],
        request=FreeTextPlanParserRequestSerializer,
        responses={200: code_response("IrrigationPlanFromTextResponse", data=FreeTextPlanParserResponseDataSerializer())},
    )
    def post(self, request):
        serializer = FreeTextPlanParserRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data.copy()

        farm_uuid = payload.get("farm_uuid")
        if farm_uuid:
            farm = self._get_farm(request, farm_uuid)
            payload["farm_uuid"] = str(farm.farm_uuid)

        adapter_response = external_api_request(
            "ai",
            "/api/irrigation/plan-from-text/",
            method="POST",
            payload=payload,
        )

        response_data = adapter_response.data if isinstance(adapter_response.data, dict) else {"message": str(adapter_response.data)}
        if adapter_response.status_code >= 400:
            return Response(
                {"code": adapter_response.status_code, "msg": "error", "data": response_data},
                status=adapter_response.status_code,
            )

        return Response(
            {"code": 200, "msg": response_data.get("msg", "موفق"), "data": response_data.get("data", response_data)},
            status=status.HTTP_200_OK,
        )
