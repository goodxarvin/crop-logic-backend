from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from external_api_adapter.adapter import AdapterResponse
from farm_hub.models import FarmHub, FarmType

from .views import IrrigationMethodListView, WaterStressView


class WaterStressViewTests(TestCase):
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

    @patch("irrigation_recommendation.views.external_api_request")
    def test_post_proxies_request_to_ai_service(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={
                "data": {
                    "result": {
                        "waterStressIndex": 12,
                        "level": "پایین",
                        "sourceMetric": {"soilMoisture": 24},
                    }
                }
            },
        )

        request = self.factory.post(
            "/api/irrigation/water-stress/",
            {"farm_uuid": str(self.farm.farm_uuid)},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = WaterStressView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(response.data["msg"], "success")
        self.assertEqual(response.data["data"]["farm_uuid"], str(self.farm.farm_uuid))
        self.assertEqual(response.data["data"]["waterStressIndex"], 12)
        self.assertEqual(response.data["data"]["level"], "پایین")
        self.assertEqual(response.data["data"]["sourceMetric"], {"soilMoisture": 24})
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/irrigation/water-stress/",
            method="POST",
            payload={"farm_uuid": str(self.farm.farm_uuid)},
        )

    def test_post_rejects_foreign_farm_uuid(self):
        request = self.factory.post(
            "/api/irrigation/water-stress/",
            {"farm_uuid": str(self.other_farm.farm_uuid)},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = WaterStressView.as_view()(request)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["code"], 404)
        self.assertEqual(response.data["data"]["farm_uuid"][0], "Farm not found.")


class IrrigationMethodListViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    @patch("irrigation_recommendation.views.external_api_request")
    def test_get_proxies_irrigation_methods_from_ai(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={
                "data": [
                    {
                        "id": 1,
                        "name": "Drip",
                        "category": "micro",
                        "description": "Efficient irrigation",
                        "water_efficiency_percent": 90.0,
                    }
                ]
            },
        )

        request = self.factory.get("/api/irrigation/")
        response = IrrigationMethodListView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(response.data["data"][0]["name"], "Drip")
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/irrigation/",
            method="GET",
        )

    @patch("irrigation_recommendation.views.external_api_request")
    def test_post_proxies_irrigation_method_creation_to_ai(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=201,
            data={
                "data": {
                    "id": 1,
                    "name": "Drip",
                    "category": "micro",
                }
            },
        )

        request = self.factory.post("/api/irrigation/", {"name": "Drip"}, format="json")
        response = IrrigationMethodListView.as_view()(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["name"], "Drip")
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/irrigation/",
            method="POST",
            payload={"name": "Drip"},
        )
