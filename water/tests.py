from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import Resolver404, resolve
from rest_framework.test import APIRequestFactory, force_authenticate

from external_api_adapter.adapter import AdapterResponse
from farm_hub.models import FarmHub, FarmType

from .views import WaterNeedPredictionView, WeatherFarmCardView


class WeatherViewTests(TestCase):
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

    @patch("water.views.external_api_request")
    def test_farm_card_proxies_to_ai_service(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={"data": {"result": {"condition": "صاف", "temperature": 28.0}}},
        )

        request = self.factory.post("/api/weather/farm-card/", {"farm_uuid": str(self.farm.farm_uuid)}, format="json")
        force_authenticate(request, user=self.user)

        response = WeatherFarmCardView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(response.data["data"]["condition"], "صاف")
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/weather/farm-card/",
            method="POST",
            payload={"farm_uuid": str(self.farm.farm_uuid)},
        )

    @patch("water.views.external_api_request")
    def test_get_water_need_prediction_uses_same_ai_service_for_farm_uuid(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={"data": {"result": {"totalNext7Days": 24.6, "unit": "mm"}}},
        )

        request = self.factory.get(f"/api/water/need-prediction/?farm_uuid={self.farm.farm_uuid}")

        response = WaterNeedPredictionView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["farm_uuid"], str(self.farm.farm_uuid))
        self.assertEqual(response.data["data"]["totalNext7Days"], 24.6)
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/weather/water-need-prediction/",
            method="POST",
            payload={"farm_uuid": str(self.farm.farm_uuid)},
        )

    def test_weather_view_rejects_foreign_farm_uuid(self):
        request = self.factory.post("/api/weather/farm-card/", {"farm_uuid": str(self.other_farm.farm_uuid)}, format="json")
        force_authenticate(request, user=self.user)

        response = WeatherFarmCardView.as_view()(request)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["code"], 404)

    def test_weather_post_routes_exist_only_under_weather_prefix(self):
        self.assertIs(resolve("/api/weather/farm-card/").func.view_class, WeatherFarmCardView)

        with self.assertRaises(Resolver404):
            resolve("/api/water/farm-card/")

        with self.assertRaises(Resolver404):
            resolve("/api/water/water-need-prediction/")

    def test_water_get_routes_do_not_exist_under_weather_prefix(self):
        with self.assertRaises(Resolver404):
            resolve("/api/weather/card/")

        with self.assertRaises(Resolver404):
            resolve("/api/weather/need-prediction/")

        with self.assertRaises(Resolver404):
            resolve("/api/weather/water-need-prediction/")

        with self.assertRaises(Resolver404):
            resolve("/api/weather/stress-index/")

        with self.assertRaises(Resolver404):
            resolve("/api/weather/summary/")
