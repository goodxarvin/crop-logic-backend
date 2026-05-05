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

from config.integration_contract import build_integration_meta
from config.swagger import code_response, status_response
from external_api_adapter import request as external_api_request
from farm_hub.models import FarmHub
from farmer_calendar import PLAN_TYPE_IRRIGATION, delete_plan_events, sync_plan_events
from water.serializers import WaterStressIndexSerializer
from water.views import WaterStressIndexView
from .defaults import CONFIG_RESPONSE_TEMPLATE
from .models import IrrigationPlan, IrrigationRecommendationRequest
from .serializers import (
    FreeTextPlanParserRequestSerializer,
    FreeTextPlanParserResponseDataSerializer,
    IrrigationMethodSerializer,
    IrrigationPlanDetailSerializer,
    IrrigationPlanListItemSerializer,
    IrrigationPlanListQuerySerializer,
    IrrigationPlanStatusUpdateSerializer,
    IrrigationRecommendationListItemSerializer,
    IrrigationRecommendationListQuerySerializer,
    IrrigationRecommendRequestSerializer,
    IrrigationRecommendResponseDataSerializer,
    WaterStressRequestSerializer,
)
from .services import build_recommendation_response
from .services import build_active_plan_context
from .services import IrrigationDataUnavailableError


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
        data = dict(CONFIG_RESPONSE_TEMPLATE)
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
            {
                "code": 200,
                "msg": "success",
                "data": self._extract_methods(adapter_response.data),
                "meta": build_integration_meta(
                    flow_type="direct_proxy",
                    source_type="provider",
                    source_service="ai_irrigation",
                    ownership="ai",
                    live=True,
                    cached=False,
                ),
            },
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
            {
                "code": adapter_response.status_code,
                "msg": "success",
                "data": payload,
                "meta": build_integration_meta(
                    flow_type="direct_proxy",
                    source_type="provider",
                    source_service="ai_irrigation",
                    ownership="ai",
                    live=True,
                    cached=False,
                ),
            },
            status=adapter_response.status_code,
        )


class RecommendView(FarmAccessMixin, APIView):
    @staticmethod
    def _build_plan_title(crop_id, growth_stage, plan):
        best_time = ""
        if isinstance(plan, dict):
            best_time = str(plan.get("bestTimeOfDay") or "").strip()
        parts = [part for part in [crop_id, growth_stage, best_time] if part]
        return " - ".join(parts) if parts else "برنامه آبیاری"

    def _create_plan_from_recommendation(self, recommendation, recommendation_data):
        plan = IrrigationPlan.objects.create(
            farm=recommendation.farm,
            source=IrrigationPlan.SOURCE_RECOMMENDATION,
            recommendation=recommendation,
            title=self._build_plan_title(recommendation.crop_id, recommendation.growth_stage, recommendation_data.get("plan")),
            crop_id=recommendation.crop_id,
            growth_stage=recommendation.growth_stage,
            plan_payload=recommendation_data,
            request_payload=recommendation.request_payload,
            response_payload=recommendation.response_payload,
        )
        sync_plan_events(plan, PLAN_TYPE_IRRIGATION)

    @staticmethod
    def _enrich_ai_payload(payload, farm):
        enriched_payload = payload.copy()
        try:
            active_plan_context = build_active_plan_context(farm)
        except IrrigationDataUnavailableError:
            active_plan_context = None
        if active_plan_context:
            enriched_payload["active_irrigation_plan"] = active_plan_context
        return enriched_payload

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

        ai_payload = self._enrich_ai_payload(payload, farm)

        adapter_response = external_api_request(
            "ai",
            "/api/irrigation/recommend/",
            method="POST",
            payload=ai_payload,
        )

        response_data = adapter_response.data if isinstance(adapter_response.data, dict) else {}
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
            request_payload=ai_payload,
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
        try:
            recommendation_data = build_recommendation_response(response_data)
        except IrrigationDataUnavailableError as exc:
            recommendation.status = IrrigationRecommendationRequest.STATUS_ERROR
            recommendation.save(update_fields=["status"])
            return Response(
                {"code": 502, "msg": "error", "data": {"detail": str(exc)}},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        logger.warning(
            "Irrigation recommendation response parsed: farm_uuid=%s status_code=%s response_keys=%s sections_count=%s",
            str(farm.farm_uuid),
            adapter_response.status_code,
            sorted(response_data.keys()) if isinstance(response_data, dict) else None,
            len(recommendation_data["sections"]),
        )

        self._create_plan_from_recommendation(recommendation, recommendation_data)

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
                "meta": build_integration_meta(
                    flow_type="backend_owned_data_with_ai_enrichment",
                    source_type="provider",
                    source_service="ai_irrigation",
                    ownership="backend",
                    live=True,
                    cached=False,
                ),
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
        recommendations = farm.irrigations.all().order_by("-created_at", "-id")

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

        try:
            data = build_recommendation_response(recommendation.response_payload)
        except IrrigationDataUnavailableError as exc:
            return Response(
                {"code": 502, "msg": "error", "data": {"detail": str(exc)}},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        request_payload = recommendation.request_payload if isinstance(recommendation.request_payload, dict) else {}
        data["recommendation_uuid"] = str(recommendation.uuid)
        data["crop_id"] = recommendation.crop_id
        data["plant_name"] = recommendation.crop_id
        data["growth_stage"] = recommendation.growth_stage
        data["irrigation_method_name"] = str(request_payload.get("irrigation_method_name") or "")
        data["status"] = recommendation.status
        data["status_label"] = recommendation.get_status_display()
        return Response(
            {
                "code": 200,
                "msg": "success",
                "data": data,
                "meta": build_integration_meta(
                    flow_type="backend_owned_data_with_ai_enrichment",
                    source_type="db",
                    source_service="backend_irrigation",
                    ownership="backend",
                    live=False,
                    cached=False,
                ),
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
            {
                "code": 200,
                "msg": "success",
                "data": stress_payload,
                "meta": build_integration_meta(
                    flow_type="direct_proxy",
                    source_type="provider",
                    source_service="ai_irrigation_water_stress",
                    ownership="ai",
                    live=True,
                    cached=False,
                ),
            },
            status=status.HTTP_200_OK,
        )


class PlanFromTextView(FarmAccessMixin, APIView):
    @staticmethod
    def _extract_final_plan(response_data):
        if not isinstance(response_data, dict):
            return None
        data = response_data.get("data")
        if isinstance(data, dict):
            final_plan = data.get("final_plan")
            if isinstance(final_plan, dict) and final_plan:
                return final_plan
        final_plan = response_data.get("final_plan")
        if isinstance(final_plan, dict) and final_plan:
            return final_plan
        return None

    @staticmethod
    def _build_free_text_plan_title(final_plan):
        if not isinstance(final_plan, dict):
            return "برنامه آبیاری"
        for key in ("title", "plan_title", "crop_name", "crop_id", "plant_name"):
            value = str(final_plan.get(key, "")).strip()
            if value:
                return value
        return "برنامه آبیاری"

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

        final_plan = self._extract_final_plan(response_data)
        if final_plan and farm_uuid:
            plan = IrrigationPlan.objects.create(
                farm=farm,
                source=IrrigationPlan.SOURCE_FREE_TEXT,
                title=self._build_free_text_plan_title(final_plan),
                crop_id=str(
                    final_plan.get("crop_id")
                    or final_plan.get("crop_name")
                    or final_plan.get("plant_name")
                    or ""
                ).strip(),
                growth_stage=str(final_plan.get("growth_stage") or "").strip(),
                plan_payload=final_plan,
                request_payload=payload,
                response_payload=response_data,
            )
            sync_plan_events(plan, PLAN_TYPE_IRRIGATION)

        return Response(
            {
                "code": 200,
                "msg": response_data.get("msg", "موفق"),
                "data": response_data.get("data", response_data),
                "meta": build_integration_meta(
                    flow_type="direct_proxy",
                    source_type="provider",
                    source_service="ai_irrigation_plan_parser",
                    ownership="backend" if final_plan and farm_uuid else "ai",
                    live=True,
                    cached=False,
                ),
            },
            status=status.HTTP_200_OK,
        )


class IrrigationPlanListView(FarmAccessMixin, APIView):
    pagination_class = IrrigationRecommendationPagination

    @extend_schema(
        tags=["Irrigation Recommendation"],
        parameters=[IrrigationPlanListQuerySerializer],
        responses={200: code_response("IrrigationPlanListResponse")},
    )
    def get(self, request):
        serializer = IrrigationPlanListQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        farm = self._get_farm(request, serializer.validated_data["farm_uuid"])
        plans = farm.irrigation_plans.filter(is_deleted=False).order_by("-created_at", "-id")

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(plans, request, view=self)
        data = IrrigationPlanListItemSerializer(page, many=True).data
        return paginator.get_paginated_response(data)


class IrrigationPlanDetailView(APIView):
    @extend_schema(
        tags=["Irrigation Recommendation"],
        parameters=[
            OpenApiParameter(
                name="plan_uuid",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                required=True,
            )
        ],
        responses={200: code_response("IrrigationPlanDetailResponse", data=IrrigationPlanDetailSerializer())},
    )
    def get(self, request, plan_uuid):
        plan = IrrigationPlan.objects.filter(
            uuid=plan_uuid,
            farm__owner=request.user,
            is_deleted=False,
        ).select_related("farm").first()
        if plan is None:
            return Response({"code": 404, "msg": "Plan not found."}, status=status.HTTP_404_NOT_FOUND)

        data = IrrigationPlanDetailSerializer(plan).data
        return Response({"code": 200, "msg": "success", "data": data}, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Irrigation Recommendation"],
        responses={200: status_response("IrrigationPlanDeleteResponse", data=serializers.JSONField())},
    )
    def delete(self, request, plan_uuid):
        plan = IrrigationPlan.objects.filter(
            uuid=plan_uuid,
            farm__owner=request.user,
            is_deleted=False,
        ).first()
        if plan is None:
            return Response({"code": 404, "msg": "Plan not found."}, status=status.HTTP_404_NOT_FOUND)

        plan.soft_delete()
        delete_plan_events(farm=plan.farm, plan_type=PLAN_TYPE_IRRIGATION, plan_uuid=plan.uuid)
        return Response({"code": 200, "msg": "success", "data": {"plan_uuid": str(plan.uuid), "is_deleted": True}}, status=status.HTTP_200_OK)


class IrrigationPlanStatusView(APIView):
    @extend_schema(
        tags=["Irrigation Recommendation"],
        request=IrrigationPlanStatusUpdateSerializer,
        responses={200: code_response("IrrigationPlanStatusResponse", data=serializers.JSONField())},
    )
    def patch(self, request, plan_uuid):
        serializer = IrrigationPlanStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan = IrrigationPlan.objects.filter(
            uuid=plan_uuid,
            farm__owner=request.user,
            is_deleted=False,
        ).first()
        if plan is None:
            return Response({"code": 404, "msg": "Plan not found."}, status=status.HTTP_404_NOT_FOUND)

        new_is_active = serializer.validated_data["is_active"]
        if new_is_active:
            IrrigationPlan.objects.filter(
                farm=plan.farm,
                is_deleted=False,
                is_active=True,
            ).exclude(pk=plan.pk).update(is_active=False)

        plan.is_active = new_is_active
        plan.save(update_fields=["is_active", "updated_at"])
        if plan.is_active:
            sync_plan_events(plan, PLAN_TYPE_IRRIGATION)
        else:
            delete_plan_events(farm=plan.farm, plan_type=PLAN_TYPE_IRRIGATION, plan_uuid=plan.uuid)
        return Response(
            {"code": 200, "msg": "success", "data": {"plan_uuid": str(plan.uuid), "is_active": plan.is_active}},
            status=status.HTTP_200_OK,
        )
