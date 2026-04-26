from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from config.swagger import farm_uuid_query_param, status_response
from external_api_adapter import request as external_api_request
from farm_hub.models import FarmHub

from .serializers import (
    SoilAnomalyDetectionSerializer,
    SoilKpiSerializer,
    SoilMoistureHeatmapSerializer,
    SoilSummarySerializer,
)
from .services import (
    get_anomaly_detection_card_data,
    get_avg_soil_moisture_data,
    get_soil_moisture_heatmap_data,
)


def _get_farm_from_request(request):
    farm_uuid = request.query_params.get("farm_uuid")
    if not farm_uuid:
        return None
    try:
        return FarmHub.objects.get(farm_uuid=farm_uuid)
    except (FarmHub.DoesNotExist, Exception):
        return None


def _extract_adapter_result(adapter_data):
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


class AvgSoilMoistureView(APIView):
    @extend_schema(
        tags=["Soil"],
        parameters=[
            farm_uuid_query_param(required=False, description="UUID of the farm for average soil moisture."),
        ],
        responses={200: status_response("AvgSoilMoistureResponse", data=SoilKpiSerializer())},
    )
    def get(self, request):
        return Response(
            {"status": "success", "data": get_avg_soil_moisture_data(_get_farm_from_request(request))},
            status=status.HTTP_200_OK,
        )


class SoilAnomalyDetectionView(APIView):
    @extend_schema(
        tags=["Soil"],
        parameters=[
            farm_uuid_query_param(required=True, description="UUID of the farm for soil anomaly detection."),
        ],
        responses={200: status_response("SoilAnomalyDetectionResponse", data=SoilAnomalyDetectionSerializer())},
    )
    def get(self, request):
        farm_uuid = request.query_params.get("farm_uuid")
        if not farm_uuid:
            return Response(
                {"code": 400, "msg": "error", "data": {"farm_uuid": ["This field is required."]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        farm = _get_farm_from_request(request)
        if farm is None:
            return Response(
                {"code": 404, "msg": "error", "data": {"farm_uuid": ["Farm not found."]}},
                status=status.HTTP_404_NOT_FOUND,
            )

        adapter_response = external_api_request(
            "ai",
            "/api/soile/anomaly-detection/",
            method="POST",
            payload={"farm_uuid": str(farm.farm_uuid)},
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
            {"code": 200, "msg": "success", "data": _extract_adapter_result(adapter_response.data)},
            status=status.HTTP_200_OK,
        )


class SoilMoistureHeatmapView(APIView):
    @extend_schema(
        tags=["Soil"],
        parameters=[
            farm_uuid_query_param(required=True, description="UUID of the farm for soil moisture heatmap."),
        ],
        responses={200: status_response("SoilMoistureHeatmapResponse", data=SoilMoistureHeatmapSerializer())},
    )
    def get(self, request):
        farm_uuid = request.query_params.get("farm_uuid")
        if not farm_uuid:
            return Response(
                {"code": 400, "msg": "error", "data": {"farm_uuid": ["This field is required."]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        farm = _get_farm_from_request(request)
        if farm is None:
            return Response(
                {"code": 404, "msg": "error", "data": {"farm_uuid": ["Farm not found."]}},
                status=status.HTTP_404_NOT_FOUND,
            )

        adapter_response = external_api_request(
            "ai",
            "/api/soile/moisture-heatmap/",
            method="POST",
            payload={"farm_uuid": str(farm.farm_uuid)},
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
            {"code": 200, "msg": "success", "data": _extract_adapter_result(adapter_response.data)},
            status=status.HTTP_200_OK,
        )


class SoilSummaryView(APIView):
    @extend_schema(
        tags=["Soil"],
        parameters=[
            farm_uuid_query_param(required=True, description="UUID of the farm for soil health summary."),
        ],
        responses={200: status_response("SoilSummaryResponse", data=SoilSummarySerializer())},
    )
    def get(self, request):
        farm_uuid = request.query_params.get("farm_uuid")
        if not farm_uuid:
            return Response(
                {"code": 400, "msg": "error", "data": {"farm_uuid": ["This field is required."]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        farm = _get_farm_from_request(request)
        if farm is None:
            return Response(
                {"code": 404, "msg": "error", "data": {"farm_uuid": ["Farm not found."]}},
                status=status.HTTP_404_NOT_FOUND,
            )

        adapter_response = external_api_request(
            "ai",
            "/api/soile/health-summary/",
            method="POST",
            payload={"farm_uuid": str(farm.farm_uuid)},
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
            {"code": 200, "msg": "success", "data": _extract_adapter_result(adapter_response.data)},
            status=status.HTTP_200_OK,
        )
