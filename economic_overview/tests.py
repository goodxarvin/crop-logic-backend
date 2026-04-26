from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import Resolver404, resolve
from rest_framework.test import APIRequestFactory, force_authenticate

from external_api_adapter.adapter import AdapterResponse
from farm_hub.models import FarmHub, FarmType

from .views import EconomyOverviewView


class EconomyOverviewViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            username="farmer",
            password="secret123",
            email="farmer@example.com",
            phone_number="09120000000",
        )
        self.other_user = get_user_model().objects.create_user(
            username="other-farmer",
            password="secret123",
            email="other@example.com",
            phone_number="09120000001",
        )
        self.farm_type = FarmType.objects.create(name="زراعی")
        self.farm = FarmHub.objects.create(owner=self.user, farm_type=self.farm_type, name="Farm 1")
        self.other_farm = FarmHub.objects.create(owner=self.other_user, farm_type=self.farm_type, name="Farm 2")

    @patch("economic_overview.views.external_api_request")
    def test_overview_proxies_to_ai_service(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={
                "data": {
                    "result": {
                        "source": "mock",
                        "economicData": [{"title": "Revenue", "value": "10"}],
                        "chartSeries": [{"name": "Revenue", "data": [1.0, 2.0]}],
                        "chartCategories": ["فروردین", "اردیبهشت"],
                    }
                }
            },
        )

        request = self.factory.post("/api/economy/overview/", {"farm_uuid": str(self.farm.farm_uuid)}, format="json")
        force_authenticate(request, user=self.user)

        response = EconomyOverviewView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(response.data["data"]["farm_uuid"], str(self.farm.farm_uuid))
        self.assertEqual(response.data["data"]["source"], "mock")
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/economy/overview/",
            method="POST",
            payload={"farm_uuid": str(self.farm.farm_uuid)},
        )

    def test_overview_rejects_foreign_farm_uuid(self):
        request = self.factory.post("/api/economy/overview/", {"farm_uuid": str(self.other_farm.farm_uuid)}, format="json")
        force_authenticate(request, user=self.user)

        response = EconomyOverviewView.as_view()(request)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["code"], 404)

    def test_economy_routes_exist_only_under_economy_prefix(self):
        self.assertIs(resolve("/api/economy/overview/").func.view_class, EconomyOverviewView)

        with self.assertRaises(Resolver404):
            resolve("/api/economy/summary/")

        with self.assertRaises(Resolver404):
            resolve("/api/economic-overview/summary/")
