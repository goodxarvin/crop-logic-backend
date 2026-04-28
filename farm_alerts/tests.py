from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from external_api_adapter.adapter import AdapterResponse
from farm_hub.models import FarmHub, FarmType
from notifications.models import FarmNotification

from .models import FarmAlert
from .serializers import FarmAlertsTrackerRequestSerializer
from .views import AlertTrackerView


class FarmAlertsTrackerRequestSerializerTests(SimpleTestCase):
    def test_accepts_farm_uuid_and_optional_alerts(self):
        serializer = FarmAlertsTrackerRequestSerializer(
            data={
                "farm_uuid": "11111111-1111-1111-1111-111111111111",
                "alerts": [
                    {
                        "alert_id": "soil-1",
                        "level": "warning",
                        "title": "Low moisture",
                    }
                ],
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_rejects_extra_fields(self):
        serializer = FarmAlertsTrackerRequestSerializer(
            data={
                "farm_uuid": "11111111-1111-1111-1111-111111111111",
                "unexpected": True,
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors["unexpected"][0], "This field is not allowed.")


class FarmAlertsTrackerViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            username="farm-alerts-user",
            password="secret123",
            email="farm-alerts@example.com",
            phone_number="09120000999",
        )
        self.other_user = get_user_model().objects.create_user(
            username="farm-alerts-other",
            password="secret123",
            email="farm-alerts-other@example.com",
            phone_number="09120000998",
        )
        self.farm_type = FarmType.objects.create(name="مرکبات")
        self.farm = FarmHub.objects.create(owner=self.user, farm_type=self.farm_type, name="Farm Alerts")

    @patch("farm_alerts.views.external_api_request")
    def test_tracker_persists_incoming_alerts_and_sends_recent_notifications_to_ai(self, mock_external_api_request):
        recent_notification = FarmNotification.objects.create(
            farm=self.farm,
            endpoint="tracker",
            title="Recent alert",
            message="Recent notification",
            level="warning",
        )
        old_notification = FarmNotification.objects.create(
            farm=self.farm,
            endpoint="tracker",
            title="Old alert",
            message="Old notification",
            level="info",
        )
        FarmNotification.objects.filter(id=old_notification.id).update(created_at=timezone.now() - timedelta(days=4))
        old_notification.refresh_from_db()

        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={
                "data": {
                    "headline": "وضعیت هشدارها",
                    "overview": "دو مورد نیاز به پیگیری دارد.",
                    "status_level": "warning",
                    "tracker": {"active": 2},
                    "notifications": [
                        {
                            "title": "افت رطوبت خاک",
                            "message": "تنش رطوبتی ادامه دارد.",
                            "level": "warning",
                            "suggested_action": "آبیاری جبرانی انجام شود.",
                            "source_alert_id": "soil-1",
                            "source_metric_type": "moisture",
                            "payload": {"current_value": 38.5},
                        }
                    ],
                    "structured_context": {"source": "ai"},
                }
            },
        )

        request = self.factory.post(
            "/api/farm-alerts/tracker/",
            {
                "farm_uuid": str(self.farm.farm_uuid),
                "alerts": [
                    {
                        "alert_id": "soil-1",
                        "level": "danger",
                        "title": "افت رطوبت خاک",
                        "message": "رطوبت خاک کمتر از حد مطلوب است.",
                        "suggested_action": "آبیاری اصلاحی بررسی شود.",
                        "source_metric_type": "moisture",
                        "payload": {"current_value": 38.5},
                    }
                ],
            },
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = AlertTrackerView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(FarmAlert.objects.filter(farm=self.farm).count(), 1)

        saved_alert = FarmAlert.objects.get(farm=self.farm)
        self.assertEqual(saved_alert.external_alert_id, "soil-1")
        self.assertEqual(saved_alert.color, "error")
        self.assertEqual(saved_alert.source_metric_type, "moisture")

        mock_external_api_request.assert_called_once()
        outbound_payload = mock_external_api_request.call_args.kwargs["payload"]
        self.assertEqual(outbound_payload["farm_uuid"], str(self.farm.farm_uuid))
        self.assertEqual(len(outbound_payload["alerts"]), 1)
        self.assertEqual(len(outbound_payload["recent_notifications"]), 1)
        self.assertEqual(outbound_payload["recent_notifications"][0]["id"], recent_notification.id)

        self.assertEqual(response.data["data"]["headline"], "وضعیت هشدارها")
        self.assertEqual(response.data["data"]["status_level"], "warning")
        self.assertEqual(len(response.data["data"]["notifications"]), 1)
        self.assertEqual(response.data["data"]["notifications"][0]["endpoint"], "tracker")

        persisted_notification = FarmNotification.objects.filter(
            farm=self.farm,
            title="افت رطوبت خاک",
            endpoint="tracker",
        ).latest("id")
        self.assertEqual(persisted_notification.source_alert_id, "soil-1")
        self.assertEqual(persisted_notification.suggested_action, "آبیاری جبرانی انجام شود.")

    @patch("farm_alerts.views.external_api_request")
    def test_tracker_limits_recent_notifications_to_ten(self, mock_external_api_request):
        for index in range(12):
            FarmNotification.objects.create(
                farm=self.farm,
                endpoint="tracker",
                title=f"Notification {index}",
                message="msg",
            )

        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={"data": {"headline": "", "overview": "", "status_level": "info", "notifications": []}},
        )

        request = self.factory.post(
            "/api/farm-alerts/tracker/",
            {"farm_uuid": str(self.farm.farm_uuid)},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = AlertTrackerView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        outbound_payload = mock_external_api_request.call_args.kwargs["payload"]
        self.assertEqual(len(outbound_payload["recent_notifications"]), 10)

    def test_tracker_rejects_unowned_farm(self):
        request = self.factory.post(
            "/api/farm-alerts/tracker/",
            {"farm_uuid": str(self.farm.farm_uuid)},
            format="json",
        )
        force_authenticate(request, user=self.other_user)

        response = AlertTrackerView.as_view()(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["farm_uuid"][0], "Farm not found.")
