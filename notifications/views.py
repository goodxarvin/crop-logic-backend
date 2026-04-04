from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from config.swagger import code_response
from farm_hub.models import FarmHub

from .serializers import FarmNotificationSerializer
from .services import create_notification_for_farm_uuid, long_poll_notifications


class NotificationLongPollQuerySerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField()
    since_id = serializers.IntegerField(required=False, min_value=1)
    timeout = serializers.IntegerField(required=False, min_value=0, max_value=60)


class ExternalNotificationCreateSerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField()
    title = serializers.CharField(max_length=255)
    message = serializers.CharField()
    level = serializers.CharField(max_length=32, required=False, default="info")
    metadata = serializers.JSONField(required=False)


class NotificationLongPollView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Notifications"],
        parameters=[NotificationLongPollQuerySerializer],
        responses={
            200: code_response("NotificationLongPollResponse", data=FarmNotificationSerializer(many=True)),
            404: code_response("NotificationLongPollNotFoundResponse"),
            503: code_response("NotificationLongPollNotificationsUnavailableResponse"),
        },
    )
    def get(self, request):
        serializer = NotificationLongPollQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        farm = FarmHub.objects.filter(
            farm_uuid=serializer.validated_data["farm_uuid"],
            owner=request.user,
        ).first()
        if farm is None:
            return Response({"code": 404, "msg": "Farm not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            notifications = long_poll_notifications(
                farm=farm,
                since_id=serializer.validated_data.get("since_id"),
                timeout_seconds=serializer.validated_data.get("timeout", 15),
            )
        except ValueError as exc:
            if str(exc) == "Notifications table is not migrated.":
                return Response(
                    {"code": 503, "msg": "Notifications table is not ready. Run migrations."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            raise
        data = FarmNotificationSerializer(notifications, many=True).data
        return Response({"code": 200, "msg": "success", "data": data}, status=status.HTTP_200_OK)


