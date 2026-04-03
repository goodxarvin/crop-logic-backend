import json
import time

from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from config.swagger import code_response

from .serializers import NotificationPublishSerializer
from .services import get_notifications_redis_client, publish_notification


def _sse_event(event_name, data):
    return f"event: {event_name}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


class NotificationStreamView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Notifications"],
        parameters=[
            OpenApiParameter(
                name="channel",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Redis channel to subscribe. Default is user-{current_user_id}.",
            ),
        ],
        responses={200: OpenApiTypes.STR},
    )
    def get(self, request):
        channel = request.query_params.get("channel") or f"user-{request.user.id}"

        def stream():
            redis_client = get_notifications_redis_client()
            pubsub = redis_client.pubsub()
            pubsub.subscribe(channel)
            try:
                yield ": connected\n\n"
                while True:
                    message = pubsub.get_message(ignore_subscribe_messages=True, timeout=15.0)
                    if message and message.get("type") == "message":
                        try:
                            payload = json.loads(message["data"])
                        except (TypeError, json.JSONDecodeError):
                            payload = {
                                "event": "notification",
                                "message": str(message["data"]),
                            }
                        yield _sse_event(payload.get("event", "notification"), payload)
                    else:
                        yield ": keepalive\n\n"
                    time.sleep(0.1)
            except GeneratorExit:
                return
            finally:
                pubsub.close()

        response = StreamingHttpResponse(stream(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response


class NotificationPublishView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Notifications"],
        request=NotificationPublishSerializer,
        responses={200: code_response("NotificationPublishResponse", data=OpenApiTypes.OBJECT)},
    )
    def post(self, request):
        serializer = NotificationPublishSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = publish_notification(**serializer.validated_data)
        return Response({"code": 200, "msg": "success", "data": payload}, status=status.HTTP_200_OK)
