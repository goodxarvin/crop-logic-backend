from rest_framework import serializers, status
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from config.swagger import code_response, farm_uuid_query_param
from farm_hub.models import FarmHub

from soil.serializers import SoilComparisonChartSerializer, SoilRadarChartSerializer
from .serializers import (
    Sensor7In1SummarySerializer,
    SensorComparisonChartQuerySerializer,
    SensorComparisonChartResponseSerializer,
    SensorRadarChartQuerySerializer,
    SensorRadarChartResponseSerializer,
    SensorValuesListQuerySerializer,
    SensorValuesListResponseSerializer,
)
from .services import (
    get_sensor_comparison_chart_data,
    get_sensor_7_in_1_comparison_chart_data,
    get_sensor_7_in_1_radar_chart_data,
    get_sensor_7_in_1_summary_data,
    get_primary_soil_sensor,
    get_sensor_radar_chart_data,
    get_sensor_values_list_data,
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

    @staticmethod
    def _get_primary_sensor(*, farm):
        sensor = get_primary_soil_sensor(farm=farm)
        if sensor is None:
            raise serializers.ValidationError({"farm_uuid": ["No sensor found for this farm."]})
        return sensor

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


class SensorComparisonChartView(Sensor7In1SummaryView):
    @extend_schema(
        tags=["Sensor 7 in 1"],
        parameters=[
            farm_uuid_query_param(required=True, description="UUID of the farm."),
            OpenApiParameter(
                name="range",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Chart range, supported values: 7d, 30d. Defaults to 7d.",
            ),
        ],
        responses={200: SensorComparisonChartResponseSerializer},
    )
    def get(self, request):
        serializer = SensorComparisonChartQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        farm = self._get_farm(request)
        sensor = self._get_primary_sensor(farm=farm)
        data = get_sensor_comparison_chart_data(
            farm=farm,
            physical_device_uuid=sensor.physical_device_uuid,
            range_value=serializer.validated_data["range"],
        )
        return Response(data, status=status.HTTP_200_OK)


class SensorValuesListView(Sensor7In1SummaryView):
    @extend_schema(
        tags=["Sensor 7 in 1"],
        parameters=[
            farm_uuid_query_param(required=True, description="UUID of the farm."),
            OpenApiParameter(
                name="range",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Values list range, supported values: 1h, 24h, 7d. Defaults to 7d.",
            ),
        ],
        responses={200: SensorValuesListResponseSerializer},
    )
    def get(self, request):
        serializer = SensorValuesListQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        farm = self._get_farm(request)
        sensor = self._get_primary_sensor(farm=farm)
        data = get_sensor_values_list_data(
            farm=farm,
            physical_device_uuid=sensor.physical_device_uuid,
            range_value=serializer.validated_data["range"],
        )
        return Response(data, status=status.HTTP_200_OK)


class SensorRadarChartView(Sensor7In1SummaryView):
    @extend_schema(
        tags=["Sensor 7 in 1"],
        parameters=[
            farm_uuid_query_param(required=True, description="UUID of the farm."),
            OpenApiParameter(
                name="range",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Radar chart range, supported values: today, 7d, 30d. Defaults to 7d.",
            ),
        ],
        responses={200: SensorRadarChartResponseSerializer},
    )
    def get(self, request):
        serializer = SensorRadarChartQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        farm = self._get_farm(request)
        sensor = self._get_primary_sensor(farm=farm)
        data = get_sensor_radar_chart_data(
            farm=farm,
            physical_device_uuid=sensor.physical_device_uuid,
            range_value=serializer.validated_data["range"],
        )
        return Response(data, status=status.HTTP_200_OK)
