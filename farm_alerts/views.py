from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from external_api_adapter import request as external_api_request

from .serializers import AlertTimelineSerializer, AlertTrackerSerializer


class FarmAlertsBaseView(APIView):
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


class AlertTrackerView(FarmAlertsBaseView):
    def post(self, request):
        adapter_response = external_api_request(
            "ai",
            "/api/farm-alerts/tracker/",
            method="POST",
            payload=request.data,
        )
        if adapter_response.status_code >= 400:
            return self._error_response(adapter_response)

        payload = self._extract_result(adapter_response.data)
        serializer = AlertTrackerSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        return Response({"code": 200, "msg": "success", "data": serializer.validated_data}, status=status.HTTP_200_OK)


class AlertTimelineView(FarmAlertsBaseView):
    def post(self, request):
        adapter_response = external_api_request(
            "ai",
            "/api/farm-alerts/timeline/",
            method="POST",
            payload=request.data,
        )
        if adapter_response.status_code >= 400:
            return self._error_response(adapter_response)

        payload = self._extract_result(adapter_response.data)
        serializer = AlertTimelineSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        return Response(
            {"code": 200, "msg": "success", "data": serializer.validated_data},
            status=status.HTTP_200_OK,
        )
