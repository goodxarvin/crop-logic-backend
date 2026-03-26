from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from config.swagger import code_response
from .models import Sensor
from .serializers import SensorCreateSerializer, SensorSerializer, SensorToggleSerializer


class SensorHubBaseView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_sensor(self, request, uuid):
        try:
            return Sensor.objects.get(uuid_sensor=uuid, owner=request.user)
        except Sensor.DoesNotExist:
            return None


class SensorListCreateView(SensorHubBaseView):
    @extend_schema(
        tags=["Sensor Hub"],
        responses={200: code_response("SensorListResponse", data=SensorSerializer(many=True))},
    )
    def get(self, request):
        sensors = Sensor.objects.filter(owner=request.user)
        data = SensorSerializer(sensors, many=True).data
        return Response({"code": 200, "msg": "success", "data": data}, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Sensor Hub"],
        request=SensorCreateSerializer,
        responses={201: code_response("SensorCreateResponse", data=SensorSerializer())},
    )
    def post(self, request):
        serializer = SensorCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sensor = serializer.save(owner=request.user)
        data = SensorSerializer(sensor).data
        return Response({"code": 201, "msg": "success", "data": data}, status=status.HTTP_201_CREATED)


class SensorDetailView(SensorHubBaseView):
    @extend_schema(
        tags=["Sensor Hub"],
        responses={
            200: code_response("SensorDetailResponse", data=SensorSerializer()),
            404: code_response("SensorNotFoundResponse"),
        },
    )
    def get(self, request, uuid):
        sensor = self._get_sensor(request, uuid)
        if sensor is None:
            return Response({"code": 404, "msg": "Sensor not found."}, status=status.HTTP_404_NOT_FOUND)
        data = SensorSerializer(sensor).data
        return Response({"code": 200, "msg": "success", "data": data}, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Sensor Hub"],
        request=SensorCreateSerializer,
        responses={
            200: code_response("SensorUpdateResponse", data=SensorSerializer()),
            404: code_response("SensorUpdateNotFoundResponse"),
        },
    )
    def patch(self, request, uuid):
        sensor = self._get_sensor(request, uuid)
        if sensor is None:
            return Response({"code": 404, "msg": "Sensor not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = SensorCreateSerializer(sensor, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data = SensorSerializer(sensor).data
        return Response({"code": 200, "msg": "success", "data": data}, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Sensor Hub"],
        responses={
            200: code_response("SensorDeleteResponse"),
            404: code_response("SensorDeleteNotFoundResponse"),
        },
    )
    def delete(self, request, uuid):
        sensor = self._get_sensor(request, uuid)
        if sensor is None:
            return Response({"code": 404, "msg": "Sensor not found."}, status=status.HTTP_404_NOT_FOUND)
        sensor.delete()
        return Response({"code": 200, "msg": "success"}, status=status.HTTP_200_OK)


class SensorToggleView(SensorHubBaseView):
    action = None

    @extend_schema(
        tags=["Sensor Hub"],
        request=SensorToggleSerializer,
        responses={
            200: code_response("SensorToggleResponse"),
            400: code_response("SensorToggleValidationResponse"),
            404: code_response("SensorToggleNotFoundResponse"),
        },
    )
    def post(self, request):
        serializer = SensorToggleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sensor = self._get_sensor(request, serializer.validated_data["uuid_sensor"])
        if sensor is None:
            return Response({"code": 404, "msg": "Sensor not found."}, status=status.HTTP_404_NOT_FOUND)

        sensor.is_active = self.action == "active"
        sensor.save(update_fields=["is_active", "updated_at"])
        return Response({"code": 200, "msg": "success"}, status=status.HTTP_200_OK)


class SensorActiveView(SensorToggleView):
    action = "active"


class SensorDeactiveView(SensorToggleView):
    action = "deactive"
