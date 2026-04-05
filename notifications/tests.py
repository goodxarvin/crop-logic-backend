from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory, force_authenticate

from farm_hub.models import FarmHub, FarmType

from .models import FarmNotification
from .services import create_notification_for_farm_uuid, long_poll_notifications, mark_notifications_as_read
from .views import ExternalNotificationIngestView, NotificationLongPollView, NotificationMarkReadView


class NotificationServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="notif-service-user",
            password="secret123",
            email="notif-service@example.com",
            phone_number="09120000011",
        )
        self.farm_type = FarmType.objects.create(name="گلخانه")
        self.farm = FarmHub.objects.create(
            owner=self.user,
            farm_type=self.farm_type,
            name="Farm A",
        )

    def test_create_notification_for_farm_uuid_creates_record(self):
        notification = create_notification_for_farm_uuid(
            farm_uuid=self.farm.farm_uuid,
            title="Irrigation alert",
            message="Soil moisture dropped",
            level="warning",
            metadata={"sensor": "soil-1"},
        )

        self.assertEqual(notification.farm, self.farm)
        self.assertEqual(notification.level, "warning")
        self.assertEqual(notification.metadata["sensor"], "soil-1")

    def test_create_notification_for_farm_uuid_raises_for_unknown_farm(self):
        with self.assertRaisesMessage(ValueError, "Farm not found."):
            create_notification_for_farm_uuid(
                farm_uuid="11111111-1111-1111-1111-111111111111",
                title="x",
                message="y",
            )

    def test_long_poll_notifications_returns_new_notifications(self):
        FarmNotification.objects.create(farm=self.farm, title="A", message="B")

        notifications = long_poll_notifications(farm=self.farm, timeout_seconds=0)

        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0].title, "A")

    def test_mark_notifications_as_read_marks_until_slice_id(self):
        first = FarmNotification.objects.create(farm=self.farm, title="A", message="B")
        second = FarmNotification.objects.create(farm=self.farm, title="C", message="D")
        third = FarmNotification.objects.create(farm=self.farm, title="E", message="F")

        marked_count = mark_notifications_as_read(farm=self.farm, slice_id=second.id)

        self.assertEqual(marked_count, 2)
        first.refresh_from_db()
        second.refresh_from_db()
        third.refresh_from_db()
        self.assertTrue(first.is_read)
        self.assertTrue(second.is_read)
        self.assertFalse(third.is_read)


class NotificationLongPollViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            username="notif-view-user",
            password="secret123",
            email="notif-view@example.com",
            phone_number="09120000012",
        )
        self.other_user = get_user_model().objects.create_user(
            username="notif-other-user",
            password="secret123",
            email="notif-other@example.com",
            phone_number="09120000013",
        )
        self.farm_type = FarmType.objects.create(name="دامداری")
        self.farm = FarmHub.objects.create(
            owner=self.user,
            farm_type=self.farm_type,
            name="Farm B",
        )

    def test_long_poll_view_returns_notifications_for_owned_farm(self):
        notification = FarmNotification.objects.create(farm=self.farm, title="Alert", message="Check sensor")
        request = self.factory.get(f"/api/notifications/long-poll/?farm_uuid={self.farm.farm_uuid}&timeout=0")
        force_authenticate(request, user=self.user)

        response = NotificationLongPollView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["title"], "Alert")
        self.assertEqual(response.data["data"][0]["since_id"], notification.id)
        self.assertFalse(response.data["data"][0]["is_read"])

    def test_long_poll_view_returns_404_for_unowned_farm(self):
        request = self.factory.get(f"/api/notifications/long-poll/?farm_uuid={self.farm.farm_uuid}&timeout=0")
        force_authenticate(request, user=self.other_user)

        response = NotificationLongPollView.as_view()(request)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["msg"], "Farm not found.")

    @patch("notifications.views.long_poll_notifications")
    def test_long_poll_view_passes_since_id(self, mocked_long_poll):
        mocked_long_poll.return_value = []
        request = self.factory.get(
            f"/api/notifications/long-poll/?farm_uuid={self.farm.farm_uuid}&since_id=5&timeout=0"
        )
        force_authenticate(request, user=self.user)

        response = NotificationLongPollView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        mocked_long_poll.assert_called_once()
        self.assertEqual(mocked_long_poll.call_args.kwargs["since_id"], 5)


class NotificationMarkReadViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            username="notif-mark-user",
            password="secret123",
            email="notif-mark@example.com",
            phone_number="09120000015",
        )
        self.other_user = get_user_model().objects.create_user(
            username="notif-mark-other-user",
            password="secret123",
            email="notif-mark-other@example.com",
            phone_number="09120000016",
        )
        self.farm_type = FarmType.objects.create(name="باغ")
        self.farm = FarmHub.objects.create(
            owner=self.user,
            farm_type=self.farm_type,
            name="Farm D",
        )

    def test_mark_read_view_marks_notifications_up_to_slice_id(self):
        first = FarmNotification.objects.create(farm=self.farm, title="Alert 1", message="Check sensor")
        second = FarmNotification.objects.create(farm=self.farm, title="Alert 2", message="Check pump")
        third = FarmNotification.objects.create(farm=self.farm, title="Alert 3", message="Check valve")
        request = self.factory.post(
            "/api/notifications/mark-as-read/",
            {
                "farm_uuid": str(self.farm.farm_uuid),
                "slice_id": second.id,
            },
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = NotificationMarkReadView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["marked_count"], 2)
        first.refresh_from_db()
        second.refresh_from_db()
        third.refresh_from_db()
        self.assertTrue(first.is_read)
        self.assertTrue(second.is_read)
        self.assertFalse(third.is_read)

    def test_mark_read_view_returns_404_for_unowned_farm(self):
        notification = FarmNotification.objects.create(farm=self.farm, title="Alert", message="Check sensor")
        request = self.factory.post(
            "/api/notifications/mark-as-read/",
            {
                "farm_uuid": str(self.farm.farm_uuid),
                "slice_id": notification.id,
            },
            format="json",
        )
        force_authenticate(request, user=self.other_user)

        response = NotificationMarkReadView.as_view()(request)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["msg"], "Farm not found.")


@override_settings(EXTERNAL_NOTIFICATION_API_KEY="12345")
class ExternalNotificationIngestViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            username="notif-external-user",
            password="secret123",
            email="notif-external@example.com",
            phone_number="09120000014",
        )
        self.farm_type = FarmType.objects.create(name="آبی")
        self.farm = FarmHub.objects.create(
            owner=self.user,
            farm_type=self.farm_type,
            name="Farm C",
        )

    def test_external_ingest_requires_api_key(self):
        request = self.factory.post(
            "/api/notifications/external/ingest/",
            {
                "farm_uuid": str(self.farm.farm_uuid),
                "title": "external",
                "message": "payload",
            },
            format="json",
        )

        response = ExternalNotificationIngestView.as_view()(request)

        self.assertEqual(response.status_code, 401)

    def test_external_ingest_creates_notification_with_valid_api_key(self):
        request = self.factory.post(
            "/api/notifications/external/ingest/",
            {
                "farm_uuid": str(self.farm.farm_uuid),
                "title": "Pump alert",
                "message": "Pump disconnected",
                "level": "critical",
                "metadata": {"source": "external-service"},
            },
            format="json",
            HTTP_X_API_KEY=settings.EXTERNAL_NOTIFICATION_API_KEY,
        )

        response = ExternalNotificationIngestView.as_view()(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["title"], "Pump alert")
        self.assertTrue(
            FarmNotification.objects.filter(farm=self.farm, title="Pump alert", level="critical").exists()
        )

    def test_external_ingest_returns_404_for_unknown_farm(self):
        request = self.factory.post(
            "/api/notifications/external/ingest/",
            {
                "farm_uuid": "11111111-1111-1111-1111-111111111111",
                "title": "Pump alert",
                "message": "Pump disconnected",
            },
            format="json",
            HTTP_X_API_KEY=settings.EXTERNAL_NOTIFICATION_API_KEY,
        )

        response = ExternalNotificationIngestView.as_view()(request)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["msg"], "Farm not found.")
