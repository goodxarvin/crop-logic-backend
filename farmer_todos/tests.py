from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from access_control.models import SubscriptionPlan
from farm_hub.models import FarmHub, FarmType

from .models import FarmerTodoTask, FarmerTodoZone
from .views import (
    FarmerTodoDetailView,
    FarmerTodoListCreateView,
    FarmerTodoSummaryView,
    FarmerTodoTagsView,
    FarmerTodoZonesView,
)


class FarmerTodoViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            username="todo-user",
            password="secret123",
            email="todo@example.com",
            phone_number="09123333333",
        )
        self.other_user = get_user_model().objects.create_user(
            username="todo-other",
            password="secret123",
            email="todo-other@example.com",
            phone_number="09124444444",
        )
        self.plan = SubscriptionPlan.objects.create(code="todo-plan", name="Todo Plan")
        self.farm_type = FarmType.objects.create(name="باغی")
        self.farm = FarmHub.objects.create(
            owner=self.user,
            farm_type=self.farm_type,
            subscription_plan=self.plan,
            name="Farm A",
        )
        self.other_farm = FarmHub.objects.create(
            owner=self.other_user,
            farm_type=self.farm_type,
            subscription_plan=self.plan,
            name="Farm B",
        )
        self.zone = FarmerTodoZone.objects.create(
            farm=self.farm,
            label="قطعه گندم - شمال مزرعه",
            value="قطعه گندم - شمال مزرعه",
        )
        self.task = FarmerTodoTask.objects.create(
            farm=self.farm,
            zone=self.zone,
            uuid="11111111-1111-1111-1111-111111111111",
            title="بررسی رطوبت ردیف شمالی",
            scheduled_date=date.today(),
            time=time(6, 30),
            priority=FarmerTodoTask.PRIORITY_HIGH,
            description="اگر رطوبت کمتر از 28٪ بود، آبیاری دوباره بررسی شود.",
            status=FarmerTodoTask.STATUS_OPEN,
            extended_props={"tags": ["آبیاری"]},
        )

    def test_list_tasks_returns_expected_shape(self):
        request = self.factory.get(f"/api/farmer-todos/?farm_uuid={self.farm.farm_uuid}")
        force_authenticate(request, user=self.user)

        response = FarmerTodoListCreateView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["meta"]["total"], 1)
        self.assertEqual(response.data["tasks"][0]["zone"], self.zone.value)
        self.assertEqual(response.data["tasks"][0]["priority"], "زیاد")
        self.assertEqual(response.data["tasks"][0]["time"], "06:30")
        self.assertEqual(str(response.data["tasks"][0]["id"]), str(self.task.uuid))

    def test_create_task_creates_zone_and_tags(self):
        request = self.factory.post(
            "/api/farmer-todos/",
            {
                "farm_uuid": str(self.farm.farm_uuid),
                "title": "بازدید پمپ جنوب",
                "zone": "انبار مرکزی",
                "scheduledDate": "2025-02-24",
                "time": "07:00",
                "priority": "medium",
                "note": "بعد از ثبت انجام، مورد غیرعادی را یادداشت کن.",
                "tags": ["روزانه", "ثبت دستی"],
                "status": "open",
            },
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = FarmerTodoListCreateView.as_view()(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["task"]["priority"], "متوسط")
        self.assertEqual(response.data["task"]["zone"], "انبار مرکزی")
        self.assertEqual(response.data["task"]["tags"], ["روزانه", "ثبت دستی"])
        self.assertTrue(FarmerTodoZone.objects.filter(farm=self.farm, value="انبار مرکزی").exists())

    def test_update_task_supports_status_only_payload(self):
        request = self.factory.put(
            f"/api/farmer-todos/{self.task.uuid}/",
            {"status": "done"},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = FarmerTodoDetailView.as_view()(request, task_id=self.task.uuid)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["task"]["status"], "done")

    def test_filter_by_search_and_priority(self):
        FarmerTodoTask.objects.create(
            farm=self.farm,
            zone=self.zone,
            title="نمونه برداری خاک",
            scheduled_date=date(2025, 2, 25),
            time=time(9, 15),
            priority=FarmerTodoTask.PRIORITY_LOW,
            description="سه نقطه برداشت شود.",
            status=FarmerTodoTask.STATUS_OPEN,
        )
        request = self.factory.get(
            f"/api/farmer-todos/?farm_uuid={self.farm.farm_uuid}&priority=high&search=رطوبت"
        )
        force_authenticate(request, user=self.user)

        response = FarmerTodoListCreateView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["meta"]["total"], 1)
        self.assertEqual(response.data["tasks"][0]["title"], "بررسی رطوبت ردیف شمالی")

    def test_zones_and_tags_endpoints_return_separate_lists(self):
        zone_request = self.factory.get(f"/api/farmer-todos/zones/?farm_uuid={self.farm.farm_uuid}")
        tag_request = self.factory.get(f"/api/farmer-todos/tags/?farm_uuid={self.farm.farm_uuid}")
        force_authenticate(zone_request, user=self.user)
        force_authenticate(tag_request, user=self.user)

        zone_response = FarmerTodoZonesView.as_view()(zone_request)
        tag_response = FarmerTodoTagsView.as_view()(tag_request)

        self.assertEqual(zone_response.status_code, 200)
        self.assertEqual(tag_response.status_code, 200)
        self.assertEqual(zone_response.data["zones"][0]["value"], self.zone.value)
        self.assertTrue(any(item["value"] == "آبیاری" for item in tag_response.data["tags"]))

    def test_summary_returns_expected_counts(self):
        FarmerTodoTask.objects.create(
            farm=self.farm,
            zone=self.zone,
            title="کار انجام شده",
            scheduled_date=date.today(),
            time=time(8, 0),
            priority=FarmerTodoTask.PRIORITY_MEDIUM,
            description="",
            status=FarmerTodoTask.STATUS_DONE,
        )
        upcoming = FarmerTodoTask.objects.create(
            farm=self.farm,
            zone=self.zone,
            title="کار بعدی",
            scheduled_date=date.today() + timedelta(days=1),
            time=time(7, 0),
            priority=FarmerTodoTask.PRIORITY_HIGH,
            description="",
            status=FarmerTodoTask.STATUS_OPEN,
        )
        request = self.factory.get(f"/api/farmer-todos/summary/?farm_uuid={self.farm.farm_uuid}")
        force_authenticate(request, user=self.user)

        response = FarmerTodoSummaryView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["completedCount"], 1)
        self.assertEqual(response.data["urgentCount"], 2)
        self.assertEqual(str(response.data["nextTask"]["id"]), str(self.task.uuid))
        self.assertNotEqual(str(response.data["nextTask"]["id"]), str(upcoming.uuid))

    def test_delete_task_returns_success(self):
        request = self.factory.delete(f"/api/farmer-todos/{self.task.uuid}/")
        force_authenticate(request, user=self.user)

        response = FarmerTodoDetailView.as_view()(request, task_id=self.task.uuid)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"success": True})
        self.assertFalse(FarmerTodoTask.objects.filter(pk=self.task.pk).exists())

    def test_validation_error_returns_message_and_details(self):
        request = self.factory.post(
            "/api/farmer-todos/",
            {
                "farm_uuid": str(self.farm.farm_uuid),
                "title": "",
                "priority": "unknown",
            },
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = FarmerTodoListCreateView.as_view()(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "TASK_VALIDATION_ERROR")
        self.assertIn("message", response.data)
        self.assertIn("details", response.data)

    def test_detail_rejects_foreign_task(self):
        foreign_zone = FarmerTodoZone.objects.create(
            farm=self.other_farm,
            label="foreign zone",
            value="foreign zone",
        )
        foreign_task = FarmerTodoTask.objects.create(
            farm=self.other_farm,
            zone=foreign_zone,
            uuid="22222222-2222-2222-2222-222222222222",
            title="foreign task",
            scheduled_date=date(2025, 2, 24),
            time=time(6, 30),
            priority=FarmerTodoTask.PRIORITY_HIGH,
            status=FarmerTodoTask.STATUS_OPEN,
        )
        request = self.factory.get(f"/api/farmer-todos/{foreign_task.uuid}/")
        force_authenticate(request, user=self.user)

        response = FarmerTodoDetailView.as_view()(request, task_id=foreign_task.uuid)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["message"], "Task not found.")
