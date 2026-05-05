from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from external_api_adapter.adapter import AdapterResponse
from farm_hub.models import FarmHub, FarmType
from notifications.models import FarmNotification

from .models import FarmAlert, FarmAlertTrackerSnapshot
from .serializers import FarmAlertsTrackerRequestSerializer
from .services import sync_farm_tracker_with_ai
from .views import AlertTrackerView


class FarmAlertsTrackerRequestSerializerTests(SimpleTestCase):
    def test_accepts_farm_uuid_and_optional_alerts(self):
        serializer = FarmAlertsTrackerRequestSerializer(
            data={
                "farm_uuid": "11111111-1111-1111-1111-111111111111",
                "alerts": [],
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

    def test_tracker_returns_cached_snapshot_without_accepting_alerts(self):
        FarmNotification.objects.create(
            farm=self.farm,
            endpoint="tracker",
            title="AI alert",
            message="Cached notification",
            level="warning",
        )
        FarmAlertTrackerSnapshot.objects.create(
            farm=self.farm,
            headline="وضعیت هشدارها",
            overview="دو مورد نیاز به پیگیری دارد.",
            status_level="warning",
            tracker={"active": 2},
            raw_llm_response='{"headline":"cached"}',
            structured_context={"source": "ai"},
        )

        request = self.factory.post(
            "/api/farm-alerts/tracker/",
            {"farm_uuid": str(self.farm.farm_uuid)},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = AlertTrackerView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["headline"], "وضعیت هشدارها")
        self.assertEqual(response.data["data"]["status_level"], "warning")
        self.assertEqual(len(response.data["data"]["notifications"]), 1)
        self.assertEqual(response.data["data"]["notifications"][0]["endpoint"], "tracker")
        self.assertEqual(response.data["meta"]["flow_type"], "cached_snapshot")
        self.assertTrue(response.data["meta"]["cached"])
        self.assertEqual(response.data["meta"]["ownership"], "backend")

    def test_tracker_limits_cached_notifications_to_ten(self):
        for index in range(12):
            FarmNotification.objects.create(farm=self.farm, endpoint="tracker", title=f"Notification {index}", message="msg")
        FarmAlertTrackerSnapshot.objects.create(farm=self.farm)

        request = self.factory.post(
            "/api/farm-alerts/tracker/",
            {"farm_uuid": str(self.farm.farm_uuid)},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = AlertTrackerView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]["notifications"]), 10)

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

    @patch("farm_alerts.services.external_api_request")
    def test_sync_task_sends_last_five_notifications_to_ai_and_updates_snapshot(self, mock_external_api_request):
        for index in range(6):
            FarmNotification.objects.create(
                farm=self.farm,
                endpoint="irrigation",
                title=f"Irrigation reminder {index}",
                message=f"Run irrigation cycle {index}",
                level="info" if index % 2 == 0 else "warning",
            )
        FarmNotification.objects.create(
            farm=self.farm,
            endpoint="irrigation",
            title="AI generated tracker notice",
            message="Should be excluded from AI input",
            level="info",
            metadata={"source": "farm_alerts_tracker_ai"},
        )

        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={
                "data": {
                    "headline": "وضعیت جدید",
                    "overview": "یک تغییر جدید شناسایی شد.",
                    "status_level": "warning",
                    "tracker": {"active": 1},
                    "notifications": [
                        {
                            "title": "افت رطوبت خاک",
                            "message": "تنش رطوبتی ادامه دارد.",
                            "level": "warning",
                            "suggested_action": "آبیاری جبرانی انجام شود.",
                            "source_alert_id": "soil-1",
                        }
                    ],
                    "structured_context": {"source": "ai"},
                }
            },
        )

        result = sync_farm_tracker_with_ai(farm=self.farm)

        self.assertEqual(result["status"], "synced")
        mock_external_api_request.assert_called_once()
        outbound_payload = mock_external_api_request.call_args.kwargs["payload"]
        self.assertEqual(outbound_payload["farm_uuid"], str(self.farm.farm_uuid))
        self.assertNotIn("alerts", outbound_payload)
        self.assertEqual(len(outbound_payload["recent_notifications"]), 5)
        self.assertEqual(outbound_payload["recent_notifications"][0]["title"], "Irrigation reminder 5")
        self.assertEqual(outbound_payload["recent_notifications"][-1]["title"], "Irrigation reminder 1")

        snapshot = FarmAlertTrackerSnapshot.objects.get(farm=self.farm)
        self.assertEqual(snapshot.headline, "وضعیت جدید")
        self.assertEqual(snapshot.status_level, "warning")
        self.assertIsNotNone(snapshot.last_ai_synced_at)
        self.assertIsNotNone(snapshot.last_source_update_at)

        persisted_notification = FarmNotification.objects.filter(
            farm=self.farm,
            title="افت رطوبت خاک",
            endpoint="tracker",
        ).latest("id")
        self.assertEqual(persisted_notification.metadata["source"], "farm_alerts_tracker_ai")

    @patch("farm_alerts.services.external_api_request")
    def test_sync_task_skips_ai_when_no_new_data_exists(self, mock_external_api_request):
        snapshot = FarmAlertTrackerSnapshot.objects.create(
            farm=self.farm,
            last_ai_synced_at=timezone.now(),
            last_source_update_at=timezone.now(),
        )
        notification = FarmNotification.objects.create(
            farm=self.farm,
            endpoint="irrigation",
            title="Irrigation reminder",
            message="Run irrigation cycle",
            level="warning",
        )
        FarmNotification.objects.filter(id=notification.id).update(updated_at=snapshot.last_source_update_at - timedelta(minutes=1))

        result = sync_farm_tracker_with_ai(farm=self.farm)

        self.assertEqual(result["status"], "skipped")
        self.assertEqual(result["reason"], "no_changes")
        mock_external_api_request.assert_not_called()
