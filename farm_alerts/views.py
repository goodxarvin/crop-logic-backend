from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from config.swagger import code_response
from external_api_adapter import request as external_api_request
from farm_hub.models import FarmHub

from .serializers import AlertTrackerAIResponseSerializer, FarmAlertsTrackerRequestSerializer
from .services import AlertService, build_tracker_context, build_tracker_response


class FarmAlertsBaseView(APIView):
    permission_classes = [IsAuthenticated]

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

    @staticmethod
    def _get_farm(request, farm_uuid):
        if not farm_uuid:
            raise serializers.ValidationError({"farm_uuid": ["This field is required."]})
        try:
            return FarmHub.objects.get(farm_uuid=farm_uuid, owner=request.user)
        except FarmHub.DoesNotExist as exc:
            raise serializers.ValidationError({"farm_uuid": ["Farm not found."]}) from exc


class AlertTrackerView(FarmAlertsBaseView):
    @extend_schema(
        tags=["Farm Alerts"],
        request=FarmAlertsTrackerRequestSerializer,
        examples=[
            OpenApiExample(
                "Tracker Request",
                value={
                    "farm_uuid": "11111111-1111-1111-1111-111111111111",
                    "alerts": [
                        {
                            "alert_id": "soil-moisture-001",
                            "level": "warning",
                            "title": "افت رطوبت خاک",
                            "message": "رطوبت خاک کمتر از حد مطلوب گزارش شده است.",
                            "suggested_action": "آبیاری اصلاحی بررسی شود.",
                            "source_metric_type": "moisture",
                        }
                    ],
                },
                request_only=True,
            )
        ],
        responses={200: code_response("FarmAlertsTrackerResponse", data=AlertTrackerAIResponseSerializer())},
    )
    def post(self, request):
        request_serializer = FarmAlertsTrackerRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        farm = self._get_farm(request, request_serializer.validated_data["farm_uuid"])
        incoming_alerts = request_serializer.validated_data.get("alerts", [])
        AlertService.persist_incoming_alerts(farm=farm, alerts=incoming_alerts)

        tracker_payload = build_tracker_context(farm=farm, alerts=incoming_alerts)
        adapter_response = external_api_request(
            "ai",
            "/api/farm-alerts/tracker/",
            method="POST",
            payload=tracker_payload,
        )
        if adapter_response.status_code >= 400:
            return self._error_response(adapter_response)

        payload = self._extract_result(adapter_response.data)
        response_data = build_tracker_response(farm=farm, adapter_payload=payload)
        serializer = AlertTrackerAIResponseSerializer(instance=response_data)
        return Response({"code": 200, "msg": "success", "data": serializer.data}, status=status.HTTP_200_OK)
