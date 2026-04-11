"""
Yield & Harvest Prediction and Plant Simulator API views.
"""

from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from config.swagger import status_response
from external_api_adapter import request as external_api_request
from farm_hub.models import FarmHub
from .mock_data import CONFIG_SLIDERS_ONLY, START_RESPONSE_DATA, STATE_RESPONSE_DATA
from .models import YieldHarvestPredictionLog
from .serializers import YieldHarvestSummarySerializer, success_response, success_with_data


class ConfigView(APIView):
    @extend_schema(
        tags=["Plant Simulator"],
        responses={200: status_response("PlantSimulatorConfigResponse", data=serializers.JSONField())},
    )
    def get(self, request):
        return Response(success_with_data(CONFIG_SLIDERS_ONLY), status=status.HTTP_200_OK)


class StateView(APIView):
    @extend_schema(
        tags=["Plant Simulator"],
        responses={200: status_response("PlantSimulatorStateResponse", data=serializers.JSONField())},
    )
    def get(self, request):
        return Response(success_with_data(STATE_RESPONSE_DATA), status=status.HTTP_200_OK)


class StartView(APIView):
    @extend_schema(
        tags=["Plant Simulator"],
        request=OpenApiTypes.OBJECT,
        responses={200: status_response("PlantSimulatorStartResponse", data=serializers.JSONField())},
    )
    def post(self, request):
        return Response(success_with_data(START_RESPONSE_DATA), status=status.HTTP_200_OK)


class StopView(APIView):
    @extend_schema(
        tags=["Plant Simulator"],
        request=OpenApiTypes.OBJECT,
        responses={200: status_response("PlantSimulatorStopResponse")},
    )
    def post(self, request):
        return Response(success_response(), status=status.HTTP_200_OK)


class ResetView(APIView):
    @extend_schema(
        tags=["Plant Simulator"],
        request=OpenApiTypes.OBJECT,
        responses={200: status_response("PlantSimulatorResetResponse")},
    )
    def post(self, request):
        return Response(success_response(), status=status.HTTP_200_OK)


class EnvironmentView(APIView):
    @extend_schema(
        tags=["Plant Simulator"],
        request=OpenApiTypes.OBJECT,
        responses={200: status_response("PlantSimulatorEnvironmentResponse")},
    )
    def patch(self, request):
        return Response(success_response(), status=status.HTTP_200_OK)


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
            OpenApiParameter(
                name="farm_uuid",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                required=False,
                description="UUID of the farm for yield and harvest prediction.",
                default="11111111-1111-1111-1111-111111111111"),
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
