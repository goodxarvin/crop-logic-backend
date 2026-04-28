from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from unittest.mock import patch

from external_api_adapter.adapter import AdapterResponse
from farm_hub.models import FarmHub, FarmType, Product
from .views import PlantListView, PlantNameListView, SelectedPlantListView


class PlantApiTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            username="plant-user",
            password="secret123",
            email="plant@example.com",
            phone_number="09123334455",
        )
        self.farm_type = FarmType.objects.create(name="زراعی")

    @patch("plants.services.external_api_request")
    def test_list_syncs_plants_from_ai_and_returns_full_payload(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={
                "code": 200,
                "msg": "success",
                "data": [
                    {
                        "name": "Tomato",
                        "light": "full sun",
                        "watering": "regular",
                        "soil": "loam",
                        "temperature": "20-30",
                        "growth_stage": "vegetative",
                        "planting_season": "spring",
                        "harvest_time": "70-90 days",
                        "spacing": "45-60 cm",
                        "fertilizer": "NPK",
                        "icon": "tomato",
                        "growth_profile": {"stage_thresholds": {"flowering": 300, "fruiting": 500}},
                    }
                ],
            },
        )
        request = self.factory.get("/api/plants/")
        force_authenticate(request, user=self.user)

        response = PlantListView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(response.data["data"][0]["name"], "Tomato")
        self.assertEqual(response.data["data"][0]["icon"], "tomato")
        self.assertIn("flowering", response.data["data"][0]["growth_stages"])
        mock_external_api_request.assert_called_once_with("ai", "/api/plants/", method="GET")

    @patch("plants.views.sync_plants_from_ai")
    def test_names_endpoint_fills_default_icon_and_growth_stages(self, mock_sync_plants_from_ai):
        mock_sync_plants_from_ai.return_value = []
        product = Product.objects.create(
            farm_type=self.farm_type,
            name="Pepper",
            growth_profile={"stage_thresholds": {"fruiting": 450}},
        )
        request = self.factory.get("/api/plants/names/")
        force_authenticate(request, user=self.user)

        response = PlantNameListView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"][0]["icon"], "leaf")
        self.assertEqual(
            response.data["data"][0]["growth_stages"],
            ["initial", "vegetative", "flowering", "fruiting", "maturity"],
        )
        product.refresh_from_db()
        self.assertEqual(product.icon, "leaf")
        self.assertEqual(product.growth_stages, ["initial", "vegetative", "flowering", "fruiting", "maturity"])

    @patch("plants.views.sync_plants_from_ai")
    def test_selected_endpoint_returns_farmer_products(self, mock_sync_plants_from_ai):
        mock_sync_plants_from_ai.return_value = []
        tomato = Product.objects.create(farm_type=self.farm_type, name="Tomato", icon="leaf", growth_stages=["vegetative"])
        pepper = Product.objects.create(farm_type=self.farm_type, name="Pepper", icon="leaf", growth_stages=["flowering"])
        farm = FarmHub.objects.create(owner=self.user, farm_type=self.farm_type, name="farm-a")
        farm.products.add(pepper)

        request = self.factory.get(f"/api/plants/selected/?farm_uuid={farm.farm_uuid}")
        force_authenticate(request, user=self.user)

        response = SelectedPlantListView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["name"], "Pepper")
        self.assertEqual(set(response.data["data"][0].keys()), {"name", "icon", "growth_stages"})
        self.assertNotEqual(response.data["data"][0]["name"], tomato.name)
