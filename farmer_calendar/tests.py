from datetime import datetime, timezone

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from access_control.models import SubscriptionPlan
from farm_hub.models import FarmHub, FarmType

from .models import FarmerCalendarEvent
from .views import EventDetailView, EventListCreateView, EventTagListView


class FarmerCalendarViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            username="calendar-user",
            password="secret123",
            email="calendar@example.com",
            phone_number="09121111111",
        )
        self.other_user = get_user_model().objects.create_user(
            username="calendar-other",
            password="secret123",
            email="calendar-other@example.com",
            phone_number="09122222222",
        )
        self.plan = SubscriptionPlan.objects.create(code="calendar-plan", name="Calendar Plan")
        self.farm_type = FarmType.objects.create(name="گلخانه")
        self.farm = FarmHub.objects.create(
            owner=self.user,
            farm_type=self.farm_type,
            subscription_plan=self.plan,
            name="Greenhouse A",
        )
        self.other_farm = FarmHub.objects.create(
            owner=self.other_user,
            farm_type=self.farm_type,
            subscription_plan=self.plan,
            name="Greenhouse B",
        )
        self.event = FarmerCalendarEvent.objects.create(
            farm=self.farm,
            title="آبیاری بلوک شمالی",
            description="کنترل فشار و مدت زمان آبیاری",
            deadline=1734942600,
            start=datetime(2025, 2, 24, 6, 30, tzinfo=timezone.utc),
            end=datetime(2025, 2, 24, 8, 0, tzinfo=timezone.utc),
            extended_props={"tags": ["آبیاری"]},
        )

    def test_list_events_returns_expected_shape(self):
        request = self.factory.get(f"/api/events/?farm_uuid={self.farm.farm_uuid}")
        force_authenticate(request, user=self.user)

        response = EventListCreateView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["meta"]["total"], 1)
        self.assertEqual(response.data["events"][0]["title"], "آبیاری بلوک شمالی")
        self.assertEqual(response.data["events"][0]["tags"], ["آبیاری"])
        self.assertIn("T06:30:00Z", response.data["events"][0]["start"])

    def test_create_event_creates_tags_and_event(self):
        request = self.factory.post(
            "/api/events/",
            {
                "farm_uuid": str(self.farm.farm_uuid),
                "title": "بازدید آفت در گلخانه",
                "description": "بررسی وضعیت برگ ها و ثبت گزارش",
                "deadline": 1734971400,
                "tags": ["آفت", "فوری"],
                "start": "2025-02-24T14:00:00Z",
                "end": "2025-02-24T15:00:00Z",
                "extendedProps": {"source": "manual"},
            },
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = EventListCreateView.as_view()(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["event"]["tags"], ["آفت", "فوری"])
        self.assertEqual(response.data["event"]["extendedProps"], {"source": "manual"})
        self.assertEqual(FarmerCalendarEvent.objects.filter(farm=self.farm).count(), 2)
        self.assertEqual(response.data["event"]["tags"], ["آفت", "فوری"])

    def test_update_event_supports_drag_and_resize_payload(self):
        request = self.factory.put(
            f"/api/events/{self.event.uuid}/",
            {
                "title": self.event.title,
                "description": "اولویت بالا",
                "deadline": self.event.deadline,
                "tags": ["آبیاری", "فوری"],
                "start": "2025-02-24T15:00:00Z",
                "end": "2025-02-24T16:00:00Z",
                "extendedProps": {},
            },
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = EventDetailView.as_view()(request, event_id=self.event.uuid)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["event"]["description"], "اولویت بالا")
        self.assertIn("T15:00:00Z", response.data["event"]["start"])
        self.assertEqual(response.data["event"]["tags"], ["آبیاری", "فوری"])

    def test_delete_event_returns_success(self):
        request = self.factory.delete(f"/api/events/{self.event.uuid}/")
        force_authenticate(request, user=self.user)

        response = EventDetailView.as_view()(request, event_id=self.event.uuid)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"success": True})
        self.assertFalse(FarmerCalendarEvent.objects.filter(pk=self.event.pk).exists())

    def test_tags_endpoint_returns_separate_list(self):
        request = self.factory.get(f"/api/events/tags/?farm_uuid={self.farm.farm_uuid}")
        force_authenticate(request, user=self.user)

        response = EventTagListView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["meta"]["total"], 1)
        self.assertEqual(response.data["tags"][0]["label"], "آبیاری")
        self.assertEqual(response.data["tags"][0]["value"], "آبیاری")

    def test_validation_error_returns_message_and_details(self):
        request = self.factory.post(
            "/api/events/",
            {
                "farm_uuid": str(self.farm.farm_uuid),
                "title": "",
                "start": "2025-02-24T15:00:00Z",
                "end": "2025-02-24T14:00:00Z",
            },
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = EventListCreateView.as_view()(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "EVENT_VALIDATION_ERROR")
        self.assertIn("message", response.data)
        self.assertIn("details", response.data)

    def test_detail_rejects_foreign_event(self):
        foreign_event = FarmerCalendarEvent.objects.create(
            farm=self.other_farm,
            title="foreign",
            start=datetime(2025, 2, 24, 6, 30, tzinfo=timezone.utc),
            end=datetime(2025, 2, 24, 8, 0, tzinfo=timezone.utc),
        )
        request = self.factory.get(f"/api/events/{foreign_event.uuid}/")
        force_authenticate(request, user=self.user)

        response = EventDetailView.as_view()(request, event_id=foreign_event.uuid)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["message"], "Event not found.")
