from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from config.swagger import code_response, farm_uuid_query_param
from farm_hub.models import FarmHub

from soil.serializers import SoilComparisonChartSerializer, SoilRadarChartSerializer
from .serializers import Sensor7In1SummarySerializer
from .services import (
    get_sensor_7_in_1_comparison_chart_data,
    get_sensor_7_in_1_radar_chart_data,
    get_sensor_7_in_1_summary_data,
)


class Sensor7In1SummaryView(APIView):
    permission_classes = [IsAuthenticated]
    required_feature_code = "sensor-7-in-1"

    @staticmethod
    def _get_farm(request):
        farm_uuid = request.query_params.get("farm_uuid")
        if not farm_uuid:
            raise serializers.ValidationError({"farm_uuid": ["This field is required."]})
        try:
            return FarmHub.objects.get(farm_uuid=farm_uuid, owner=request.user)
        except FarmHub.DoesNotExist as exc:
            raise serializers.ValidationError({"farm_uuid": ["Farm not found."]}) from exc

    @extend_schema(
        tags=["Sensor 7 in 1"],
        parameters=[
            farm_uuid_query_param(required=True, description="UUID of the farm for sensor 7 in 1 summary.")
        ],
        responses={200: code_response("Sensor7In1SummaryResponse", data=Sensor7In1SummarySerializer())},
    )
    def get(self, request):
        farm = self._get_farm(request)
        return Response(
            {"code": 200, "msg": "OK", "data": get_sensor_7_in_1_summary_data(farm)},
            status=status.HTTP_200_OK,
        )


class Sensor7In1RadarChartView(Sensor7In1SummaryView):
    @extend_schema(
        tags=["Sensor 7 in 1"],
        parameters=[
            farm_uuid_query_param(required=True, description="UUID of the farm for sensor 7 in 1 radar chart.")
        ],
        responses={200: code_response("Sensor7In1RadarChartResponse", data=SoilRadarChartSerializer())},
    )
    def get(self, request):
        farm = self._get_farm(request)
        return Response(
            {"code": 200, "msg": "OK", "data": get_sensor_7_in_1_radar_chart_data(farm)},
            status=status.HTTP_200_OK,
        )


class Sensor7In1ComparisonChartView(Sensor7In1SummaryView):
    @extend_schema(
        tags=["Sensor 7 in 1"],
        parameters=[
            farm_uuid_query_param(required=True, description="UUID of the farm for sensor 7 in 1 comparison chart.")
        ],
        responses={200: code_response("Sensor7In1ComparisonChartResponse", data=SoilComparisonChartSerializer())},
    )
    def get(self, request):
        farm = self._get_farm(request)
        return Response(
            {"code": 200, "msg": "OK", "data": get_sensor_7_in_1_comparison_chart_data(farm)},
            status=status.HTTP_200_OK,
        )
