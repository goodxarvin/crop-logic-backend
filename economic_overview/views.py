import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from config.failure_contract import StructuredServiceError
from config.swagger import status_response
from external_api_adapter import request as external_api_request
from external_api_adapter.exceptions import ExternalAPIRequestError
from farm_hub.models import FarmHub
from .models import EconomicOverviewLog
from .serializers import EconomicOverviewRequestSerializer, EconomicOverviewSerializer

logger = logging.getLogger(__name__)


class EconomicOverviewAdapterError(StructuredServiceError):
    def __init__(self, *, error_code: str, message: str, source: str, retriable: bool = False, details: dict | None = None):
        super().__init__(
            error_code=error_code,
            message=message,
            source=source,
            retriable=retriable,
            details=details,
        )


class EconomyOverviewView(APIView):
    @staticmethod
    def _extract_result_or_error(adapter_data):
        if not isinstance(adapter_data, dict):
            raise EconomicOverviewAdapterError(
                error_code="invalid_payload",
                message="Economic overview adapter returned a non-object payload.",
                source="ai_provider",
            )

        data = adapter_data.get("data")
        if isinstance(data, dict) and isinstance(data.get("result"), dict):
            return data["result"]
        if isinstance(data, dict):
            return data

        result = adapter_data.get("result")
        if isinstance(result, dict):
            return result

        raise EconomicOverviewAdapterError(
            error_code="invalid_payload",
            message="Economic overview adapter payload did not contain structured result data.",
            source="ai_provider",
        )

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
    def _persist_log(farm, overview_data):
        if not isinstance(overview_data, dict):
            raise EconomicOverviewAdapterError(
                error_code="invalid_payload",
                message="Economic overview data must be a JSON object before persistence.",
                source="backend",
            )
        EconomicOverviewLog.objects.create(
            farm=farm,
            economic_data=overview_data.get("economicData", []),
            chart_series=overview_data.get("chartSeries", []),
            chart_categories=overview_data.get("chartCategories", []),
        )

    @extend_schema(
        tags=["Economy"],
        request=EconomicOverviewRequestSerializer,
        responses={200: status_response("EconomyOverviewResponse", data=EconomicOverviewSerializer())},
    )
    def post(self, request):
        serializer = EconomicOverviewRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        farm, error_response = self._get_farm(request, serializer.validated_data["farm_uuid"])
        if error_response is not None:
            return error_response

        payload = {"farm_uuid": str(farm.farm_uuid)}
        try:
            adapter_response = external_api_request(
                "ai",
                "/api/economy/overview/",
                method="POST",
                payload=payload,
            )
        except ExternalAPIRequestError as exc:
            logger.error("Economic overview upstream request failed for farm_uuid=%s: %s", farm.farm_uuid, exc)
            failure = EconomicOverviewAdapterError(
                error_code="upstream_unavailable",
                message="Economic overview upstream request failed.",
                source="ai_provider",
                retriable=True,
                details={"farm_uuid": str(farm.farm_uuid)},
            )
            return Response(
                {"code": 503, "msg": "error", "data": failure.to_dict()},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
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

        try:
            overview_data = self._extract_result_or_error(adapter_response.data)
            if isinstance(overview_data, dict):
                overview_data.setdefault("farm_uuid", str(farm.farm_uuid))
            self._persist_log(farm, overview_data)
        except EconomicOverviewAdapterError as exc:
            logger.error("Economic overview payload handling failed for farm_uuid=%s: %s", farm.farm_uuid, exc)
            return Response(
                {"code": 502, "msg": "error", "data": exc.to_dict()},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response({"code": 200, "msg": "success", "data": overview_data}, status=status.HTTP_200_OK)
