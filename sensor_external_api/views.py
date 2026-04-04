from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema

from config.swagger import code_response
from notifications.serializers import FarmNotificationSerializer

from .authentication import SensorExternalAPIKeyAuthentication
from .serializers import SensorExternalRequestSerializer
from .services import create_sensor_external_notification


class SensorExternalAPIView(APIView):
    authentication_classes = [SensorExternalAPIKeyAuthentication]
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Sensor External API"],
        request=SensorExternalRequestSerializer,
        parameters=[
            OpenApiParameter(
                name="X-API-Key",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=True,
                default="12345",
                description="API key for sensor external API.",
            )
        ],
        responses={
            201: code_response("SensorExternalAPIResponse", data=FarmNotificationSerializer()),
            401: code_response("SensorExternalAPIUnauthorizedResponse"),
            404: code_response("SensorExternalAPIFarmNotFoundResponse"),
            503: code_response("SensorExternalAPINotificationsUnavailableResponse"),
        },
    )
    def post(self, request):
        serializer = SensorExternalRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            notification = create_sensor_external_notification(payload=serializer.validated_data.get("payload"))
        except ValueError as exc:
            if str(exc) == "Notifications table is not migrated.":
                return Response(
                    {"code": 503, "msg": "Notifications table is not ready. Run migrations."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            return Response({"code": 404, "msg": "Farm not found."}, status=status.HTTP_404_NOT_FOUND)

        data = FarmNotificationSerializer(notification).data
        return Response({"code": 201, "msg": "success", "data": data}, status=status.HTTP_201_CREATED)
