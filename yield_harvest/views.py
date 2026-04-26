"""Yield & Harvest Prediction and Crop Simulation API views."""

from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from config.swagger import farm_uuid_query_param, status_response
from external_api_adapter import request as external_api_request
from farm_hub.models import FarmHub
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
            farm_uuid_query_param(required=False, description="UUID of the farm for yield and harvest prediction."),
        ],
        responses={200: status_response("YieldHarvestSummaryResponse", data=YieldHarvestSummarySerializer())},
    )
    def get(self, request):
        farm_uuid = request.query_params.get("farm_uuid")
        query = {"farm_uuid": str(farm_uuid)} if farm_uuid else {}

        adapter_response = external_api_request(
            "ai",
            "/yield-harvest/summary",
            method="GET",
            query=query,
        )

        response_data = adapter_response.data if isinstance(adapter_response.data, dict) else {}
        summary = response_data.get("result", response_data.get("data", response_data))

        self._persist_log(farm_uuid, summary)

        return Response(
            {"status": "success", "data": summary},
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

        yield_card = summary.get("yield_prediction_card", {})
        harvest_card = summary.get("harvest_prediction_card", {})

        YieldHarvestPredictionLog.objects.create(
            farm=farm,
            yield_stats=yield_card.get("stats", ""),
            yield_chip_text=yield_card.get("chipText", ""),
            harvest_date=harvest_card.get("date") or None,
            days_until_harvest=harvest_card.get("daysUntil"),
            optimal_window_start=harvest_card.get("optimalWindowStart") or None,
            optimal_window_end=harvest_card.get("optimalWindowEnd") or None,
            chart_data=summary.get("yield_prediction_chart", {}),
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


class CurrentFarmChartView(CropSimulationBaseView):
    ai_path = "/api/crop-simulation/current-farm-chart/"

    @extend_schema(
        tags=["Crop Simulation"],
        request=CropSimulationRequestSerializer,
        responses={200: status_response("CurrentFarmChartResponse", data=CurrentFarmChartSerializer())},
    )
    def post(self, request):
        serializer = CropSimulationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data.copy()

        farm, error_response = self._get_farm(request, payload.get("farm_uuid"))
        if error_response is not None:
            return error_response

        ai_payload = {"farm_uuid": str(farm.farm_uuid), "plant_name": payload.get("plant_name", "")}
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
        responses={200: status_response("CropSimulationHarvestPredictionResponse", data=HarvestPredictionSerializer())},
    )
    def post(self, request):
        serializer = CropSimulationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data.copy()

        farm, error_response = self._get_farm(request, payload.get("farm_uuid"))
        if error_response is not None:
            return error_response

        ai_payload = {"farm_uuid": str(farm.farm_uuid), "plant_name": payload.get("plant_name", "")}
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
        responses={200: status_response("CropSimulationYieldPredictionResponse", data=YieldPredictionSerializer())},
    )
    def post(self, request):
        serializer = CropSimulationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data.copy()

        farm, error_response = self._get_farm(request, payload.get("farm_uuid"))
        if error_response is not None:
            return error_response

        ai_payload = {"farm_uuid": str(farm.farm_uuid), "plant_name": payload.get("plant_name", "")}
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
        responses={202: status_response("GrowthSimulationQueuedResponse", data=GrowthSimulationQueuedDataSerializer())},
    )
    def post(self, request):
        serializer = GrowthSimulationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payload = serializer.validated_data.copy()
        if payload.get("farm_uuid") is not None:
            payload["farm_uuid"] = str(payload["farm_uuid"])

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
        responses={200: status_response("GrowthSimulationStatusResponse", data=GrowthSimulationStatusDataSerializer())},
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
