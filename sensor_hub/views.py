"""
Sensor Hub module.
All endpoints require authenticated user (must be registered).
All responses are static; no processing or validation on inputs.
"""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import SensorStoreResponseSerializer

# Static sensor payload for store (list/get) response.
STORE_DATA = {
    "name": "sensor-hub-static",
    "uuid_sensor": "550e8400-e29b-41d4-a716-446655440000",
    "last_updated": "2025-02-18T12:00:00Z",
    "specifications": {
        "model": "SH-1",
        "firmware": "1.0.0",
        "capabilities": ["temperature", "humidity", "light"],
    },
    "power_source": {
        "type": "battery",
        "voltage": 3.3,
        "backup": "solar",
    },
    "customized_sensors": {
        "thresholds": {"temperature_min": 10, "temperature_max": 35},
        "report_interval_sec": 300,
    },
}


# Static payload for single-sensor detail response (same shape as store).
SENSOR_DETAIL_DATA = {
    "name": "sensor-hub-static",
    "uuid_sensor": "550e8400-e29b-41d4-a716-446655440000",
    "last_updated": "2025-02-18T12:00:00Z",
    "specifications": {
        "model": "SH-1",
        "firmware": "1.0.0",
        "capabilities": ["temperature", "humidity", "light"],
    },
    "power_source": {
        "type": "battery",
        "voltage": 3.3,
        "backup": "solar",
    },
    "customized_sensors": {
        "thresholds": {"temperature_min": 10, "temperature_max": 35},
        "report_interval_sec": 300,
    },
}


class SensorHubView(APIView):
    """
    Sensor-hub endpoints. Behavior depends on URL and HTTP method.
    No processing or validation is performed on inputs; responses are static.

    Routes:
    - GET  ""           → List: returns code 200, msg "success", data with static sensor list.
    - GET  "<uuid>/"    → Detail: uuid (path). Returns code 200, msg "success", data with static sensor payload.
    - POST ""           → Add: body/query may be sent but not used. Returns code 200, msg "success". No data field.
    - PATCH "<uuid>/"   → Update: uuid (path), body/query may be sent but not used. Returns code 200, msg "success". No data field.
    - DELETE "<uuid>/"  → Delete: uuid (path). Returns code 200, msg "success". No data field.
    - POST "active/"    → Activate: no input. Returns code 200, msg "success". No data field.
    - POST "deactive/"  → Deactivate: no input. Returns code 200, msg "success". No data field.
    """

    # permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        uuid = kwargs.get("uuid")
        if uuid is not None:
            data = SensorStoreResponseSerializer(SENSOR_DETAIL_DATA).data
        else:
            data = SensorStoreResponseSerializer(STORE_DATA).data
        return Response({"code": 200, "msg": "success", "data": data}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        action = kwargs.get("action")
        if action == "active":
            return Response({"code": 200, "msg": "success"}, status=status.HTTP_200_OK)
        if action == "deactive":
            return Response({"code": 200, "msg": "success"}, status=status.HTTP_200_OK)
        # POST without action = add
        return Response({"code": 200, "msg": "success"}, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        return Response({"code": 200, "msg": "success"}, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        return Response({"code": 200, "msg": "success"}, status=status.HTTP_200_OK)
