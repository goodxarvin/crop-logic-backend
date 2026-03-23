from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Sensor
from .serializers import SensorCreateSerializer, SensorSerializer


class SensorHubView(APIView):
    """
    Sensor-hub CRUD endpoints connected to the database.

    Routes:
    - GET  ""           → List sensors for authenticated user.
    - GET  "<uuid>/"    → Detail of a single sensor.
    - POST ""           → Create a new sensor.
    - PATCH "<uuid>/"   → Update an existing sensor.
    - DELETE "<uuid>/"  → Delete a sensor.
    - POST "active/"    → Activate a sensor (requires uuid_sensor in body).
    - POST "deactive/"  → Deactivate a sensor (requires uuid_sensor in body).
    """

    permission_classes = [IsAuthenticated]

    def _get_sensor(self, request, uuid):
        try:
            return Sensor.objects.get(uuid_sensor=uuid, owner=request.user)
        except Sensor.DoesNotExist:
            return None

    def get(self, request, *args, **kwargs):
        uuid = kwargs.get("uuid")
        if uuid is not None:
            sensor = self._get_sensor(request, uuid)
            if sensor is None:
                return Response(
                    {"code": 404, "msg": "Sensor not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            data = SensorSerializer(sensor).data
            return Response({"code": 200, "msg": "success", "data": data}, status=status.HTTP_200_OK)

        sensors = Sensor.objects.filter(owner=request.user)
        data = SensorSerializer(sensors, many=True).data
        return Response({"code": 200, "msg": "success", "data": data}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        action = kwargs.get("action")
        if action in ("active", "deactive"):
            return self._toggle_active(request, is_active=(action == "active"))

        serializer = SensorCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sensor = serializer.save(owner=request.user)
        data = SensorSerializer(sensor).data
        return Response(
            {"code": 201, "msg": "success", "data": data},
            status=status.HTTP_201_CREATED,
        )

    def patch(self, request, *args, **kwargs):
        uuid = kwargs.get("uuid")
        sensor = self._get_sensor(request, uuid)
        if sensor is None:
            return Response(
                {"code": 404, "msg": "Sensor not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = SensorCreateSerializer(sensor, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data = SensorSerializer(sensor).data
        return Response({"code": 200, "msg": "success", "data": data}, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        uuid = kwargs.get("uuid")
        sensor = self._get_sensor(request, uuid)
        if sensor is None:
            return Response(
                {"code": 404, "msg": "Sensor not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        sensor.delete()
        return Response({"code": 200, "msg": "success"}, status=status.HTTP_200_OK)

    def _toggle_active(self, request, is_active):
        uuid_sensor = request.data.get("uuid_sensor")
        if not uuid_sensor:
            return Response(
                {"code": 400, "msg": "uuid_sensor is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        sensor = self._get_sensor(request, uuid_sensor)
        if sensor is None:
            return Response(
                {"code": 404, "msg": "Sensor not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        sensor.is_active = is_active
        sensor.save(update_fields=["is_active", "updated_at"])
        return Response({"code": 200, "msg": "success"}, status=status.HTTP_200_OK)
