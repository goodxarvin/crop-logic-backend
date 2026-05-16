from copy import deepcopy
from uuid import UUID

from django.core.exceptions import ImproperlyConfigured
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from config.swagger import code_response
from external_api_adapter.adapter import request as external_api_request
from external_api_adapter.exceptions import ExternalAPIRequestError
from farm_hub.models import FarmHub

from .serializers import (
    FarmUUIDRequestSerializer,
    KOptionActivateSerializer,
    LocationDataUpsertSerializer,
)
from .services import (
    AI_CLUSTER_RECOMMENDATIONS_PATH,
    AI_LOCATION_DATA_PATH,
    AI_REMOTE_SENSING_PATH,
)


AI_PROXY_ERROR_MESSAGE = "ارتباط با سرویس AI ناموفق بود."
FARM_NOT_FOUND_MESSAGE = "مزرعه پیدا نشد."
QUERY_FARM_NOT_FOUND_MESSAGE = "location پیدا نشد."
SUCCESS_RESPONSE = code_response("LocationDataGenericSuccess", data=serializers.JSONField())
ERROR_RESPONSE = code_response("LocationDataGenericError", data=serializers.JSONField())

LOCATION_DATA_QUERY_PARAMETERS = [
    OpenApiParameter("lat", OpenApiTypes.NUMBER, OpenApiParameter.QUERY, required=False),
    OpenApiParameter("lon", OpenApiTypes.NUMBER, OpenApiParameter.QUERY, required=False),
    OpenApiParameter("farm_uuid", OpenApiTypes.UUID, OpenApiParameter.QUERY, required=False),
]
REMOTE_SENSING_QUERY_PARAMETERS = [
    OpenApiParameter("farm_uuid", OpenApiTypes.UUID, OpenApiParameter.QUERY, required=True),
    OpenApiParameter("page", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
    OpenApiParameter("page_size", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
    OpenApiParameter("start_date", OpenApiTypes.DATE, OpenApiParameter.QUERY, required=False),
    OpenApiParameter("end_date", OpenApiTypes.DATE, OpenApiParameter.QUERY, required=False),
]
CLUSTER_BLOCK_LIVE_QUERY_PARAMETERS = [
    OpenApiParameter("start_date", OpenApiTypes.DATE, OpenApiParameter.QUERY, required=False),
    OpenApiParameter("end_date", OpenApiTypes.DATE, OpenApiParameter.QUERY, required=False),
    OpenApiParameter("farm_uuid", OpenApiTypes.UUID, OpenApiParameter.QUERY, required=False),
]
OPTIONAL_FARM_UUID_QUERY_PARAMETER = [
    OpenApiParameter("farm_uuid", OpenApiTypes.UUID, OpenApiParameter.QUERY, required=False),
]


class AILocationDataProxyView(APIView):
    ai_path = AI_LOCATION_DATA_PATH
    farm_uuid_locations = ()
    farm_not_found_message = FARM_NOT_FOUND_MESSAGE

    def _build_path(self, **kwargs):
        return self.ai_path.format(**kwargs)

    def _get_payload(self, request):
        if not request.data:
            return None
        if isinstance(request.data, dict):
            return deepcopy(request.data)
        return request.data

    def _get_query(self, request):
        if not request.query_params:
            return None
        query = {}
        for key, values in request.query_params.lists():
            query[key] = values if len(values) > 1 else values[0]
        return query

    def _parse_uuid(self, value):
        if not value:
            return None
        try:
            return UUID(str(value))
        except (TypeError, ValueError, AttributeError):
            return None

    def _extract_farm_uuid(self, request, payload, query):
        for location in self.farm_uuid_locations:
            if location == "body" and isinstance(payload, dict) and payload.get("farm_uuid"):
                parsed = self._parse_uuid(payload.get("farm_uuid"))
                if parsed is not None:
                    return parsed
            if location == "query" and isinstance(query, dict) and query.get("farm_uuid"):
                parsed = self._parse_uuid(query.get("farm_uuid"))
                if parsed is not None:
                    return parsed
        return None

    def _ensure_farm_access(self, request, farm_uuid):
        if farm_uuid is None:
            return None
        if FarmHub.objects.filter(farm_uuid=farm_uuid, owner=request.user).exists():
            return None
        return Response(
            {"code": 404, "msg": self.farm_not_found_message, "data": None},
            status=status.HTTP_404_NOT_FOUND,
        )

    def _build_proxy_error(self, exc):
        return Response(
            {"code": 502, "msg": AI_PROXY_ERROR_MESSAGE, "data": {"detail": str(exc)}},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    def _proxy(self, request, *, method, **path_kwargs):
        payload = self._get_payload(request)
        query = self._get_query(request)
        farm_uuid = self._extract_farm_uuid(request, payload, query)
        farm_error = self._ensure_farm_access(request, farm_uuid)
        if farm_error is not None:
            return farm_error

        try:
            adapter_response = external_api_request(
                "ai",
                self._build_path(**path_kwargs),
                method=method,
                payload=payload,
                query=query,
            )
        except (ExternalAPIRequestError, ImproperlyConfigured) as exc:
            return self._build_proxy_error(exc)

        response_payload = adapter_response.data
        if not isinstance(response_payload, dict):
            response_payload = {
                "code": adapter_response.status_code,
                "msg": "success" if adapter_response.status_code < 400 else "error",
                "data": response_payload,
            }
        return Response(response_payload, status=adapter_response.status_code)


class LocationDataView(AILocationDataProxyView):
    farm_uuid_locations = ("query", "body")
    farm_not_found_message = QUERY_FARM_NOT_FOUND_MESSAGE

    @extend_schema(
        tags=["Location Data"],
        parameters=LOCATION_DATA_QUERY_PARAMETERS,
        responses={200: SUCCESS_RESPONSE, 400: ERROR_RESPONSE, 404: ERROR_RESPONSE},
    )
    def get(self, request):
        return self._proxy(request, method="GET")

    @extend_schema(
        tags=["Location Data"],
        request=LocationDataUpsertSerializer,
        responses={200: SUCCESS_RESPONSE, 400: ERROR_RESPONSE, 404: ERROR_RESPONSE},
    )
    def post(self, request):
        return self._proxy(request, method="POST")


class LocationDataNdviHealthView(AILocationDataProxyView):
    ai_path = f"{AI_LOCATION_DATA_PATH}ndvi-health/"
    farm_uuid_locations = ("body",)

    @extend_schema(
        tags=["Location Data"],
        request=FarmUUIDRequestSerializer,
        responses={200: SUCCESS_RESPONSE, 400: ERROR_RESPONSE, 404: ERROR_RESPONSE},
    )
    def post(self, request):
        return self._proxy(request, method="POST")


class LocationDataRemoteSensingView(AILocationDataProxyView):
    ai_path = AI_REMOTE_SENSING_PATH
    farm_uuid_locations = ("query", "body")

    @extend_schema(
        tags=["Location Data"],
        parameters=REMOTE_SENSING_QUERY_PARAMETERS,
        responses={200: SUCCESS_RESPONSE, 400: ERROR_RESPONSE, 404: ERROR_RESPONSE},
    )
    def get(self, request):
        return self._proxy(request, method="GET")

    @extend_schema(
        tags=["Location Data"],
        request=FarmUUIDRequestSerializer,
        responses={202: SUCCESS_RESPONSE, 400: ERROR_RESPONSE, 404: ERROR_RESPONSE},
    )
    def post(self, request):
        return self._proxy(request, method="POST")


class ClusterBlockLiveView(AILocationDataProxyView):
    ai_path = f"{AI_REMOTE_SENSING_PATH}cluster-blocks/{{cluster_uuid}}/live/"
    farm_uuid_locations = ("query",)

    @extend_schema(
        tags=["Location Data"],
        parameters=CLUSTER_BLOCK_LIVE_QUERY_PARAMETERS,
        responses={200: SUCCESS_RESPONSE, 400: ERROR_RESPONSE, 404: ERROR_RESPONSE, 502: ERROR_RESPONSE},
    )
    def get(self, request, cluster_uuid):
        return self._proxy(request, method="GET", cluster_uuid=cluster_uuid)


class ClusterRecommendationsView(AILocationDataProxyView):
    ai_path = AI_CLUSTER_RECOMMENDATIONS_PATH
    farm_uuid_locations = ("query",)

    @extend_schema(
        tags=["Location Data"],
        parameters=REMOTE_SENSING_QUERY_PARAMETERS[:1],
        responses={200: SUCCESS_RESPONSE, 400: ERROR_RESPONSE, 404: ERROR_RESPONSE},
    )
    def get(self, request):
        return self._proxy(request, method="GET")


class KOptionsView(AILocationDataProxyView):
    ai_path = f"{AI_REMOTE_SENSING_PATH}results/{{result_id}}/k-options/"
    farm_uuid_locations = ("query",)

    @extend_schema(
        tags=["Location Data"],
        parameters=OPTIONAL_FARM_UUID_QUERY_PARAMETER,
        responses={200: SUCCESS_RESPONSE, 404: ERROR_RESPONSE},
    )
    def get(self, request, result_id):
        return self._proxy(request, method="GET", result_id=result_id)


class KOptionsActivateView(AILocationDataProxyView):
    ai_path = f"{AI_REMOTE_SENSING_PATH}results/{{result_id}}/k-options/activate/"
    farm_uuid_locations = ("query", "body")

    @extend_schema(
        tags=["Location Data"],
        parameters=OPTIONAL_FARM_UUID_QUERY_PARAMETER,
        request=KOptionActivateSerializer,
        responses={200: SUCCESS_RESPONSE, 400: ERROR_RESPONSE, 404: ERROR_RESPONSE},
    )
    def post(self, request, result_id):
        return self._proxy(request, method="POST", result_id=result_id)


class RunStatusView(AILocationDataProxyView):
    ai_path = f"{AI_REMOTE_SENSING_PATH}runs/{{run_id}}/status/"
    farm_uuid_locations = ("query",)

    @extend_schema(
        tags=["Location Data"],
        parameters=OPTIONAL_FARM_UUID_QUERY_PARAMETER,
        responses={200: SUCCESS_RESPONSE, 404: ERROR_RESPONSE},
    )
    def get(self, request, run_id):
        return self._proxy(request, method="GET", run_id=run_id)
