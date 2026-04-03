from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from .views import NotificationPublishView, NotificationStreamView


class NotificationPublishViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            username="notify-user",
            password="secret123",
            email="notify@example.com",
            phone_number="09120000099",
        )

    @patch("notifications.views.publish_notification")
    def test_publish_calls_service_and_returns_payload(self, mock_publish_notification):
        mock_publish_notification.return_value = {"id": "1", "event": "notification", "message": "hello"}
        request = self.factory.post(
            "/api/notifications/publish/",
            {
                "channel": "user-1",
                "title": "Test",
                "message": "hello",
                "level": "info",
            },
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = NotificationPublishView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        mock_publish_notification.assert_called_once()


class _FakePubSub:
    def __init__(self):
        self.calls = 0

    def subscribe(self, _channel):
        return None

    def get_message(self, ignore_subscribe_messages=True, timeout=15.0):
        self.calls += 1
        if self.calls == 1:
            return {"type": "message", "data": '{"event":"notification","message":"hi"}'}
        return None

    def close(self):
        return None


class _FakeRedis:
    def __init__(self):
        self._pubsub = _FakePubSub()

    def pubsub(self):
        return self._pubsub


class NotificationStreamViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            username="stream-user",
            password="secret123",
            email="stream@example.com",
            phone_number="09120000098",
        )

    @patch("notifications.views.get_notifications_redis_client")
    def test_stream_returns_event_stream_response(self, mock_redis_client):
        mock_redis_client.return_value = _FakeRedis()
        request = self.factory.get("/api/notifications/stream/?channel=user-1")
        force_authenticate(request, user=self.user)

        response = NotificationStreamView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/event-stream")
        iterator = iter(response.streaming_content)
        first_chunk = self._to_text(next(iterator))
        second_chunk = self._to_text(next(iterator))
        self.assertIn("connected", first_chunk)
        self.assertIn("event: notification", second_chunk)

    @staticmethod
    def _to_text(value):
        if isinstance(value, bytes):
            return value.decode()
        return str(value)
