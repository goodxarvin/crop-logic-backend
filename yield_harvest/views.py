"""Yield & Harvest Prediction and Crop Simulation API views."""

from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from config.swagger import code_response, farm_uuid_query_param
from external_api_adapter import request as external_api_request
from farm_hub.models import FarmHub
from fertilization.models import FertilizationPlan
from irrigation.models import IrrigationPlan
from .models import YieldHarvestPredictionLog
from .serializers import (
    CropSimulationRequestSerializer,
    CurrentFarmChartSerializer,
    GrowthSimulationQueuedDataSerializer,
    GrowthSimulationRequestSerializer,
    GrowthSimulationStatusDataSerializer,
    HarvestPredictionSerializer,
    YieldHarvestSummarySerializer,
    YieldPredictionSerializer,
)


class YieldHarvestSummaryView(APIView):
    """
    GET endpoint for combined yield prediction and harvest prediction data.

    Purpose:
        Returns three dashboard card payloads in one response:
          - yield_prediction_card  (kpi card shape)
          - yield_prediction_chart (monthly chart + summary)
          - harvest_prediction_card (harvest date + window)
        Data is fetched from the AI external adapter. If farm_uuid is provided
        and the farm exists, the result is persisted in YieldHarvestPredictionLog.

    Input parameters:
        - farm_uuid (query, optional): UUID of the farm.

    Response structure:
        - status: string, always "success".
        - data: object with keys yield_prediction_card,
          yield_prediction_chart, harvest_prediction_card.
    """

    @extend_schema(
        tags=["Yield & Harvest Prediction"],
        parameters=[
            farm_uuid_query_param(required=True, description="UUID of the farm for yield and harvest prediction."),
            OpenApiParameter(
                name="season_year",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description="سال زراعی.",
            ),
            OpenApiParameter(
                name="crop_name",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="نام محصول.",
            ),
            OpenApiParameter(
                name="include_narrative",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                required=False,
                description="در صورت true بودن متن های narrative نیز اضافه می شوند.",
            ),
        ],
        responses={200: code_response("YieldHarvestSummaryResponse", data=YieldHarvestSummarySerializer())},
    )
    def get(self, request):
        farm_uuid = request.query_params.get("farm_uuid")
        farm, error_response = CropSimulationBaseView._get_farm(request, farm_uuid)
        if error_response is not None:
            return error_response

        irrigation_plan_uuid, irrigation_plan_error = CropSimulationBaseView._parse_optional_plan_uuid(
            request.query_params.get("irrigation_plan_uuid"),
            "irrigation_plan_uuid",
        )
        if irrigation_plan_error is not None:
            return irrigation_plan_error

        fertilization_plan_uuid, fertilization_plan_error = CropSimulationBaseView._parse_optional_plan_uuid(
            request.query_params.get("fertilization_plan_uuid"),
            "fertilization_plan_uuid",
        )
        if fertilization_plan_error is not None:
            return fertilization_plan_error

        query = {"farm_uuid": str(farm.farm_uuid)}
        if request.query_params.get("season_year"):
            query["season_year"] = request.query_params.get("season_year")
        if request.query_params.get("crop_name"):
            query["crop_name"] = request.query_params.get("crop_name")
        if request.query_params.get("include_narrative") is not None:
            query["include_narrative"] = request.query_params.get("include_narrative")

        ai_payload, plan_error = CropSimulationBaseView()._build_ai_payload_with_selected_plans(
            farm,
            irrigation_plan_uuid=irrigation_plan_uuid,
            fertilization_plan_uuid=fertilization_plan_uuid,
        )
        if plan_error is not None:
            return plan_error
        query.update(ai_payload)

        adapter_response = external_api_request(
            "ai",
            "/api/crop-simulation/yield-harvest-summary/",
            method="GET",
            query=query,
        )
        if adapter_response.status_code >= 400:
            return CropSimulationBaseView._error_response(adapter_response)

        summary = CropSimulationBaseView._extract_result(adapter_response.data)

        self._persist_log(farm.farm_uuid, summary)

        return Response(
            {"code": 200, "msg": "success", "data": summary},
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _persist_log(farm_uuid, summary):
        farm = None
        if farm_uuid:
            try:
                farm = FarmHub.objects.get(farm_uuid=farm_uuid)
            except (FarmHub.DoesNotExist, Exception):
                pass

        yield_card = summary.get("yield_prediction") or summary.get("yield_prediction_card") or {}
        harvest_card = summary.get("harvest_prediction_card", {})
        yield_chart = summary.get("yield_prediction_chart", {})
        if not isinstance(yield_card, dict):
            yield_card = {}
        if not isinstance(harvest_card, dict):
            harvest_card = {}
        if not isinstance(yield_chart, dict):
            yield_chart = {}

        YieldHarvestPredictionLog.objects.create(
            farm=farm,
            yield_stats=str(yield_card.get("predicted_yield_tons") or yield_card.get("stats") or ""),
            yield_chip_text=str(yield_card.get("unit") or yield_card.get("chipText") or ""),
            harvest_date=harvest_card.get("harvest_date") or harvest_card.get("date") or None,
            days_until_harvest=harvest_card.get("days_until") or harvest_card.get("daysUntil"),
            optimal_window_start=harvest_card.get("optimal_window_start") or harvest_card.get("optimalWindowStart") or None,
            optimal_window_end=harvest_card.get("optimal_window_end") or harvest_card.get("optimalWindowEnd") or None,
            chart_data=yield_chart,
        )


class CropSimulationBaseView(APIView):
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
    def _extract_result(adapter_data):
        if not isinstance(adapter_data, dict):
            return {}

        data = adapter_data.get("data")
        if isinstance(data, dict) and isinstance(data.get("result"), dict):
            return data["result"]
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

    @staticmethod
    def _get_first_farm_product_name(farm):
        first_product = farm.products.order_by("id").first()
        if first_product is not None:
            return (first_product.name or "").strip()

        fallback_product = farm.farm_type.products.order_by("id").first()
        if fallback_product is not None:
            return (fallback_product.name or "").strip()

        return ""

    @staticmethod
    def _get_irrigation_plan_or_error(farm, plan_uuid):
        if not plan_uuid:
            return None, None

        plan = IrrigationPlan.objects.filter(
            uuid=plan_uuid,
            farm=farm,
            is_deleted=False,
        ).first()
        if plan is None:
            return None, Response(
                {"code": 404, "msg": "error", "data": {"irrigation_plan_uuid": ["Irrigation plan not found."]}},
                status=status.HTTP_404_NOT_FOUND,
            )
        return plan, None

    @staticmethod
    def _get_fertilization_plan_or_error(farm, plan_uuid):
        if not plan_uuid:
            return None, None

        plan = FertilizationPlan.objects.filter(
            uuid=plan_uuid,
            farm=farm,
            is_deleted=False,
        ).first()
        if plan is None:
            return None, Response(
                {"code": 404, "msg": "error", "data": {"fertilization_plan_uuid": ["Fertilization plan not found."]}},
                status=status.HTTP_404_NOT_FOUND,
            )
        return plan, None

    @staticmethod
    def _build_plan_payload(plan):
        if plan is None:
            return None

        return {
            "id": plan.id,
            "uuid": str(plan.uuid),
            "source": plan.source,
            "title": plan.title,
            "crop_id": plan.crop_id,
            "growth_stage": plan.growth_stage,
            "is_active": plan.is_active,
            "plan_payload": plan.plan_payload if isinstance(plan.plan_payload, dict) else {},
            "request_payload": plan.request_payload if isinstance(plan.request_payload, dict) else {},
            "response_payload": plan.response_payload if isinstance(plan.response_payload, dict) else {},
        }

    def _build_ai_payload_with_selected_plans(self, farm, irrigation_plan_uuid=None, fertilization_plan_uuid=None):
        irrigation_plan, irrigation_error = self._get_irrigation_plan_or_error(farm, irrigation_plan_uuid)
        if irrigation_error is not None:
            return None, irrigation_error

        fertilization_plan, fertilization_error = self._get_fertilization_plan_or_error(
            farm, fertilization_plan_uuid
        )
        if fertilization_error is not None:
            return None, fertilization_error

        ai_payload = {
            "farm_uuid": str(farm.farm_uuid),
            "plant_name": self._get_first_farm_product_name(farm),
        }
        if irrigation_plan is not None:
            ai_payload["irrigation_plan"] = self._build_plan_payload(irrigation_plan)
        if fertilization_plan is not None:
            ai_payload["fertilization_plan"] = self._build_plan_payload(fertilization_plan)

        return ai_payload, None

    @staticmethod
    def _parse_optional_plan_uuid(raw_value, field_name):
        if raw_value in (None, ""):
            return None, None
        try:
            parsed_value = str(serializers.UUIDField().to_internal_value(raw_value))
        except serializers.ValidationError:
            return None, Response(
                {"code": 400, "msg": "error", "data": {field_name: ["Must be a valid UUID."]}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return parsed_value, None


class CurrentFarmChartView(CropSimulationBaseView):
    ai_path = "/api/crop-simulation/current-farm-chart/"

    @extend_schema(
        tags=["Crop Simulation"],
        request=CropSimulationRequestSerializer,
        responses={200: code_response("CurrentFarmChartResponse", data=CurrentFarmChartSerializer())},
    )
    def post(self, request):
        serializer = CropSimulationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data.copy()

        farm, error_response = self._get_farm(request, payload.get("farm_uuid"))
        if error_response is not None:
            return error_response

        ai_payload, plan_error = self._build_ai_payload_with_selected_plans(
            farm,
            irrigation_plan_uuid=payload.get("irrigation_plan_uuid"),
            fertilization_plan_uuid=payload.get("fertilization_plan_uuid"),
        )
        if plan_error is not None:
            return plan_error
        adapter_response = external_api_request("ai", self.ai_path, method="POST", payload=ai_payload)

        if adapter_response.status_code >= 400:
            return self._error_response(adapter_response)

        return Response(
            {"code": 200, "msg": "success", "data": self._extract_result(adapter_response.data)},
            status=status.HTTP_200_OK,
        )


class HarvestPredictionView(CropSimulationBaseView):
    ai_path = "/api/crop-simulation/harvest-prediction/"

    @extend_schema(
        tags=["Crop Simulation"],
        request=CropSimulationRequestSerializer,
        responses={200: code_response("CropSimulationHarvestPredictionResponse", data=HarvestPredictionSerializer())},
    )
    def post(self, request):
        serializer = CropSimulationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data.copy()

        farm, error_response = self._get_farm(request, payload.get("farm_uuid"))
        if error_response is not None:
            return error_response

        ai_payload, plan_error = self._build_ai_payload_with_selected_plans(
            farm,
            irrigation_plan_uuid=payload.get("irrigation_plan_uuid"),
            fertilization_plan_uuid=payload.get("fertilization_plan_uuid"),
        )
        if plan_error is not None:
            return plan_error
        adapter_response = external_api_request("ai", self.ai_path, method="POST", payload=ai_payload)

        if adapter_response.status_code >= 400:
            return self._error_response(adapter_response)

        return Response(
            {"code": 200, "msg": "success", "data": self._extract_result(adapter_response.data)},
            status=status.HTTP_200_OK,
        )


class YieldPredictionView(CropSimulationBaseView):
    ai_path = "/api/crop-simulation/yield-prediction/"

    @extend_schema(
        tags=["Crop Simulation"],
        request=CropSimulationRequestSerializer,
        responses={200: code_response("CropSimulationYieldPredictionResponse", data=YieldPredictionSerializer())},
    )
    def post(self, request):
        serializer = CropSimulationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data.copy()

        farm, error_response = self._get_farm(request, payload.get("farm_uuid"))
        if error_response is not None:
            return error_response

        ai_payload, plan_error = self._build_ai_payload_with_selected_plans(
            farm,
            irrigation_plan_uuid=payload.get("irrigation_plan_uuid"),
            fertilization_plan_uuid=payload.get("fertilization_plan_uuid"),
        )
        if plan_error is not None:
            return plan_error
        adapter_response = external_api_request("ai", self.ai_path, method="POST", payload=ai_payload)

        if adapter_response.status_code >= 400:
            return self._error_response(adapter_response)

        return Response(
            {"code": 200, "msg": "success", "data": self._extract_result(adapter_response.data)},
            status=status.HTTP_200_OK,
        )


class GrowthSimulationView(APIView):
    @extend_schema(
        tags=["Crop Simulation"],
        request=GrowthSimulationRequestSerializer,
        responses={202: code_response("GrowthSimulationQueuedResponse", data=GrowthSimulationQueuedDataSerializer())},
    )
    def post(self, request):
        serializer = GrowthSimulationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payload = serializer.validated_data.copy()
        farm_uuid = payload.get("farm_uuid")
        if farm_uuid is not None:
            farm, error_response = CropSimulationBaseView._get_farm(request, farm_uuid)
            if error_response is not None:
                return error_response
            payload["farm_uuid"] = str(farm.farm_uuid)
            payload["plant_name"] = CropSimulationBaseView._get_first_farm_product_name(farm)

        adapter_response = external_api_request(
            "ai",
            "/api/crop-simulation/growth/",
            method="POST",
            payload=payload,
        )

        if adapter_response.status_code >= 400:
            response_data = (
                adapter_response.data
                if isinstance(adapter_response.data, dict)
                else {"message": str(adapter_response.data)}
            )
            return Response(
                {"code": adapter_response.status_code, "msg": "error", "data": response_data},
                status=adapter_response.status_code,
            )

        return Response(
            {"code": 202, "msg": "تسک شبیه سازی رشد در صف قرار گرفت.", "data": CropSimulationBaseView._extract_result(adapter_response.data)},
            status=status.HTTP_202_ACCEPTED,
        )


class GrowthSimulationStatusView(APIView):
    @extend_schema(
        tags=["Crop Simulation"],
        parameters=[
            OpenApiParameter(name="page", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, required=False, description="شماره صفحه."),
            OpenApiParameter(
                name="page_size",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description="اندازه صفحه بین 1 تا 50.",
            ),
        ],
        responses={200: code_response("GrowthSimulationStatusResponse", data=GrowthSimulationStatusDataSerializer())},
    )
    def get(self, request, task_id):
        query = {}
        if request.query_params.get("page"):
            query["page"] = request.query_params.get("page")
        if request.query_params.get("page_size"):
            query["page_size"] = request.query_params.get("page_size")

        adapter_response = external_api_request(
            "ai",
            f"/api/crop-simulation/growth/{task_id}/status/",
            method="GET",
            query=query or None,
        )

        if adapter_response.status_code >= 400:
            response_data = (
                adapter_response.data
                if isinstance(adapter_response.data, dict)
                else {"message": str(adapter_response.data)}
            )
            return Response(
                {"code": adapter_response.status_code, "msg": "error", "data": response_data},
                status=adapter_response.status_code,
            )

        return Response(
            {"code": 200, "msg": "success", "data": CropSimulationBaseView._extract_result(adapter_response.data)},
            status=status.HTTP_200_OK,
        )
