from django.conf import settings
from django.core.cache import cache
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
    SoilMonitorSerializer,
    SoilMoistureHeatmapSerializer,
    SoilSummarySerializer,
)
from .services import (
    get_anomaly_detection_card_data,
    get_avg_soil_moisture_data,
    get_soil_monitor_data,
    get_soil_moisture_heatmap_data,
)


SOIL_ANOMALIES_CACHE_KEY = "soil:anomalies:recent"
SOIL_ANOMALIES_CACHE_LIMIT = 4
SOIL_SUMMARY_CACHE_KEY = "soil:summary:recent"
SOIL_SUMMARY_CACHE_LIMIT = 4


def _store_recent_soil_anomalies(payload):
    cached_items = cache.get(SOIL_ANOMALIES_CACHE_KEY, [])
    if not isinstance(cached_items, list):
        cached_items = []

    cached_items.insert(0, payload)
    cache.set(SOIL_ANOMALIES_CACHE_KEY, cached_items[:SOIL_ANOMALIES_CACHE_LIMIT], timeout=None)


def _store_recent_soil_summary(payload):
    cached_items = cache.get(SOIL_SUMMARY_CACHE_KEY, [])
    if not isinstance(cached_items, list):
        cached_items = []

    cached_items.insert(0, payload)
    cache.set(SOIL_SUMMARY_CACHE_KEY, cached_items[:SOIL_SUMMARY_CACHE_LIMIT], timeout=None)


def _build_soil_summary_cache_key(farm_uuid):
    return f"soil:summary:{farm_uuid}"


def _build_soil_anomalies_cache_key(farm_uuid):
    return f"soil:anomalies:{farm_uuid}"



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

        cache_key = _build_soil_anomalies_cache_key(farm.farm_uuid)
        cached_anomalies = cache.get(cache_key)
        if isinstance(cached_anomalies, dict):
            return Response(
                {"code": 200, "msg": "success", "data": cached_anomalies},
                status=status.HTTP_200_OK,
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

        response_payload = _extract_adapter_result(adapter_response.data)
        cache.set(cache_key, response_payload, timeout=settings.SOIL_ANOMALIES_CACHE_TTL)
        _store_recent_soil_anomalies(response_payload)
        return Response(
            {"code": 200, "msg": "success", "data": response_payload},
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

        return Response(
            {"code": 200, "msg": "success", "data": get_soil_moisture_heatmap_data(farm)},
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

        cache_key = _build_soil_summary_cache_key(farm.farm_uuid)
        cached_summary = cache.get(cache_key)
        if isinstance(cached_summary, dict):
            return Response(
                {"code": 200, "msg": "success", "data": cached_summary},
                status=status.HTTP_200_OK,
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

        response_payload = _extract_adapter_result(adapter_response.data)
        cache.set(cache_key, response_payload, timeout=settings.SOIL_SUMMARY_CACHE_TTL)
        _store_recent_soil_summary(response_payload)
        return Response(
            {"code": 200, "msg": "success", "data": response_payload},
            status=status.HTTP_200_OK,
        )


class SoilMonitorView(APIView):
    @extend_schema(
        tags=["Soil"],
        parameters=[
            farm_uuid_query_param(required=True, description="UUID of the farm for zone-based soil monitoring."),
        ],
        responses={200: status_response("SoilMonitorResponse", data=SoilMonitorSerializer())},
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

        return Response(
            {"code": 200, "msg": "success", "data": get_soil_monitor_data(farm)},
            status=status.HTTP_200_OK,
        )
