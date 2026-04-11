from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from config.swagger import status_response
from farm_hub.models import FarmHub

from .serializers import (
    SoilAnomalyDetectionSerializer,
    SoilComparisonChartSerializer,
    SoilKpiSerializer,
    SoilMoistureHeatmapSerializer,
    SoilRadarChartSerializer,
    SoilSummarySerializer,
)
from .services import (
    get_anomaly_detection_card_data,
    get_avg_soil_moisture_data,
    get_sensor_comparison_chart_data,
    get_sensor_radar_chart_data,
    get_soil_moisture_heatmap_data,
    get_soil_summary_data,
)


def _get_farm_from_request(request):
    farm_uuid = request.query_params.get("farm_uuid")
    if not farm_uuid:
        return None
    try:
        return FarmHub.objects.get(farm_uuid=farm_uuid)
    except (FarmHub.DoesNotExist, Exception):
        return None


class AvgSoilMoistureView(APIView):
    @extend_schema(
        tags=["Soil"],
        parameters=[
            OpenApiParameter(
                name="farm_uuid",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                required=False,
                description="UUID of the farm for average soil moisture.",
                default="11111111-1111-1111-1111-111111111111",
            ),
        ],
        responses={200: status_response("AvgSoilMoistureResponse", data=SoilKpiSerializer())},
    )
    def get(self, request):
        return Response(
            {"status": "success", "data": get_avg_soil_moisture_data(_get_farm_from_request(request))},
            status=status.HTTP_200_OK,
        )


class SensorRadarChartView(APIView):
    @extend_schema(
        tags=["Soil"],
        parameters=[
            OpenApiParameter(name="farm_uuid", type=OpenApiTypes.UUID, location=OpenApiParameter.QUERY, required=False),
        ],
        responses={200: status_response("SensorRadarChartResponse", data=SoilRadarChartSerializer())},
    )
    def get(self, request):
        return Response(
            {"status": "success", "data": get_sensor_radar_chart_data(_get_farm_from_request(request))},
            status=status.HTTP_200_OK,
        )


class SensorComparisonChartView(APIView):
    @extend_schema(
        tags=["Soil"],
        parameters=[
            OpenApiParameter(name="farm_uuid", type=OpenApiTypes.UUID, location=OpenApiParameter.QUERY, required=False),
        ],
        responses={200: status_response("SensorComparisonChartResponse", data=SoilComparisonChartSerializer())},
    )
    def get(self, request):
        return Response(
            {"status": "success", "data": get_sensor_comparison_chart_data(_get_farm_from_request(request))},
            status=status.HTTP_200_OK,
        )


class SoilAnomalyDetectionView(APIView):
    @extend_schema(
        tags=["Soil"],
        parameters=[
            OpenApiParameter(name="farm_uuid", type=OpenApiTypes.UUID, location=OpenApiParameter.QUERY, required=False),
        ],
        responses={200: status_response("SoilAnomalyDetectionResponse", data=SoilAnomalyDetectionSerializer())},
    )
    def get(self, request):
        return Response(
            {"status": "success", "data": get_anomaly_detection_card_data(_get_farm_from_request(request))},
            status=status.HTTP_200_OK,
        )


class SoilMoistureHeatmapView(APIView):
    @extend_schema(
        tags=["Soil"],
        parameters=[
            OpenApiParameter(name="farm_uuid", type=OpenApiTypes.UUID, location=OpenApiParameter.QUERY, required=False),
        ],
        responses={200: status_response("SoilMoistureHeatmapResponse", data=SoilMoistureHeatmapSerializer())},
    )
    def get(self, request):
        return Response(
            {"status": "success", "data": get_soil_moisture_heatmap_data(_get_farm_from_request(request))},
            status=status.HTTP_200_OK,
        )


class SoilSummaryView(APIView):
    @extend_schema(
        tags=["Soil"],
        parameters=[
            OpenApiParameter(name="farm_uuid", type=OpenApiTypes.UUID, location=OpenApiParameter.QUERY, required=False),
        ],
        responses={200: status_response("SoilSummaryResponse", data=SoilSummarySerializer())},
    )
    def get(self, request):
        return Response(
            {"status": "success", "data": get_soil_summary_data(_get_farm_from_request(request))},
            status=status.HTTP_200_OK,
        )
