from django.conf import settings
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import serializers, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from config.swagger import code_response
from farm_hub.models import FarmHub

from .serializers import FarmNotificationSerializer
from .services import  long_poll_notifications, mark_notifications_as_read


class NotificationLongPollQuerySerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField()
    since_id = serializers.IntegerField(required=False, min_value=1)
    timeout = serializers.IntegerField(required=False, min_value=0, max_value=60)


class NotificationListQuerySerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField()
    page = serializers.IntegerField(required=False, min_value=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100)


class NotificationPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class NotificationMarkReadSerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField()
    slice_id = serializers.IntegerField(min_value=1)


def get_owned_farm(*, farm_uuid, user):
    return FarmHub.objects.filter(farm_uuid=farm_uuid, owner=user).first()


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

        farm = get_owned_farm(
            farm_uuid=serializer.validated_data["farm_uuid"],
            user=request.user,
        )
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


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = NotificationPagination

    @extend_schema(
        tags=["Notifications"],
        parameters=[NotificationListQuerySerializer],
        responses={
            200: code_response("NotificationListResponse"),
            404: code_response("NotificationListNotFoundResponse"),
        },
    )
    def get(self, request):
        serializer = NotificationListQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        farm = get_owned_farm(
            farm_uuid=serializer.validated_data["farm_uuid"],
            user=request.user,
        )
        if farm is None:
            return Response({"code": 404, "msg": "Farm not found."}, status=status.HTTP_404_NOT_FOUND)

        paginator = self.pagination_class()
        notifications = farm.notifications.all().order_by("-created_at", "-id")
        page = paginator.paginate_queryset(notifications, request, view=self)
        data = FarmNotificationSerializer(page, many=True).data

        return paginator.get_paginated_response({
            "code": 200,
            "msg": "success",
            "data": data,
        })


class NotificationMarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Notifications"],
        request=NotificationMarkReadSerializer,
        responses={
            200: code_response(
                "NotificationMarkReadResponse",
                extra_fields={"marked_count": serializers.IntegerField()},
            ),
            404: code_response("NotificationMarkReadNotFoundResponse"),
            503: code_response("NotificationMarkReadUnavailableResponse"),
        },
    )
    def post(self, request):
        serializer = NotificationMarkReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        farm = get_owned_farm(
            farm_uuid=serializer.validated_data["farm_uuid"],
            user=request.user,
        )
        if farm is None:
            return Response({"code": 404, "msg": "Farm not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            marked_count = mark_notifications_as_read(
                farm=farm,
                slice_id=serializer.validated_data["slice_id"],
            )
        except ValueError as exc:
            if str(exc) == "Notifications table is not migrated.":
                return Response(
                    {"code": 503, "msg": "Notifications table is not ready. Run migrations."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            raise

        return Response(
            {"code": 200, "msg": "success", "marked_count": marked_count},
            status=status.HTTP_200_OK,
        )

