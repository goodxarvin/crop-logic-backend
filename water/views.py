"""
WATER API views.
"""

from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from config.swagger import status_response
from external_api_adapter import request as external_api_request
from farm_hub.models import FarmHub
from .models import WeatherForecastLog
from .serializers import FarmWeatherCardSerializer, WaterNeedPredictionSerializer, WaterStressIndexSerializer, WaterSummarySerializer
from .services import get_water_need_prediction_data, get_water_stress_index_data, get_water_summary_data


class FarmWeatherCardView(APIView):
    """
    GET endpoint for the farm weather card dashboard data.

    Purpose:
        Returns current weather conditions and an intraday temperature chart
        for a given farm. Data is fetched from the AI external adapter.
        If farm_uuid is provided and the farm exists, the result is persisted
        in WeatherForecastLog for historical reference.

    Input parameters:
        - farm_uuid (query, optional): UUID of the farm.

    Response structure:
        - status: string, always "success".
        - data: object matching the farmWeatherCard shape — condition,
          temperature, unit, humidity, windSpeed, windUnit, chartData.
    """

    @extend_schema(
        tags=["WATER"],
        parameters=[
            OpenApiParameter(
                name="farm_uuid",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                required=False,
                description="UUID of the farm to fetch weather data for.",
                default="11111111-1111-1111-1111-111111111111"),
        ],
        responses={200: status_response("FarmWeatherCardResponse", data=FarmWeatherCardSerializer())},
    )
    def get(self, request):
        farm_uuid = request.query_params.get("farm_uuid")
        query = {"farm_uuid": str(farm_uuid)} if farm_uuid else {}

        adapter_response = external_api_request(
            "ai",
            "/weather-forecast/card",
            method="GET",
            query=query,
        )

        response_data = adapter_response.data if isinstance(adapter_response.data, dict) else {}
        card_data = response_data.get("result", response_data.get("data", response_data))

        self._persist_log(farm_uuid, card_data)

        return Response(
            {"status": "success", "data": card_data},
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _persist_log(farm_uuid, card_data):
        farm = None
        if farm_uuid:
            try:
                farm = FarmHub.objects.get(farm_uuid=farm_uuid)
            except (FarmHub.DoesNotExist, Exception):
                pass

        WeatherForecastLog.objects.create(
            farm=farm,
            condition=card_data.get("condition", ""),
            temperature=card_data.get("temperature"),
            unit=card_data.get("unit", "°C"),
            humidity=card_data.get("humidity"),
            wind_speed=card_data.get("windSpeed"),
            wind_unit=card_data.get("windUnit", "km/h"),
            chart_data=card_data.get("chartData", {}),
        )


class WaterNeedPredictionView(APIView):
    @extend_schema(
        tags=["WATER"],
        parameters=[
            OpenApiParameter(
                name="farm_uuid",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                required=False,
                description="UUID of the farm to fetch water need prediction for.",
                default="11111111-1111-1111-1111-111111111111",
            ),
        ],
        responses={200: status_response("WaterNeedPredictionResponse", data=WaterNeedPredictionSerializer())},
    )
    def get(self, request):
        farm = None
        farm_uuid = request.query_params.get("farm_uuid")
        if farm_uuid:
            try:
                farm = FarmHub.objects.get(farm_uuid=farm_uuid)
            except (FarmHub.DoesNotExist, Exception):
                farm = None

        return Response(
            {"status": "success", "data": get_water_need_prediction_data(farm)},
            status=status.HTTP_200_OK,
        )


class WaterStressIndexView(APIView):
    @extend_schema(
        tags=["WATER"],
        parameters=[
            OpenApiParameter(
                name="farm_uuid",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                required=False,
                description="UUID of the farm to fetch water stress index for.",
                default="11111111-1111-1111-1111-111111111111",
            ),
        ],
        responses={200: status_response("WaterStressIndexResponse", data=WaterStressIndexSerializer())},
    )
    def get(self, request):
        farm = None
        farm_uuid = request.query_params.get("farm_uuid")
        if farm_uuid:
            try:
                farm = FarmHub.objects.get(farm_uuid=farm_uuid)
            except (FarmHub.DoesNotExist, Exception):
                farm = None

        return Response(
            {"status": "success", "data": get_water_stress_index_data(farm)},
            status=status.HTTP_200_OK,
        )


class WaterSummaryView(APIView):
    @extend_schema(
        tags=["WATER"],
        parameters=[
            OpenApiParameter(
                name="farm_uuid",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                required=False,
                description="UUID of the farm to fetch water summary for.",
                default="11111111-1111-1111-1111-111111111111",
            ),
        ],
        responses={200: status_response("WaterSummaryResponse", data=WaterSummarySerializer())},
    )
    def get(self, request):
        farm = None
        farm_uuid = request.query_params.get("farm_uuid")
        if farm_uuid:
            try:
                farm = FarmHub.objects.get(farm_uuid=farm_uuid)
            except (FarmHub.DoesNotExist, Exception):
                farm = None

        return Response(
            {"status": "success", "data": get_water_summary_data(farm)},
            status=status.HTTP_200_OK,
        )
