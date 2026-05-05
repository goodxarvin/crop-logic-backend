from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from unittest.mock import patch

from farm_hub.models import FarmHub, FarmType, Product
from .services import PlantSyncError
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

    @patch("plants.views.push_plants_to_ai")
    def test_list_returns_backend_catalog_with_sync_metadata(self, mock_push_plants_to_ai):
        mock_push_plants_to_ai.return_value = []
        Product.objects.create(
            farm_type=self.farm_type,
            name="Tomato",
            icon="tomato",
            growth_stage="vegetative",
            growth_profile={"stage_thresholds": {"flowering": 300, "fruiting": 500}},
        )
        request = self.factory.get("/api/plants/")
        force_authenticate(request, user=self.user)

        response = PlantListView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(response.data["data"][0]["name"], "Tomato")
        self.assertEqual(response.data["data"][0]["icon"], "tomato")
        self.assertIn("flowering", response.data["data"][0]["growth_stages"])
        self.assertEqual(response.data["meta"]["flow_type"], "backend_owned_data_with_ai_enrichment")
        self.assertEqual(response.data["meta"]["source_type"], "db")
        self.assertEqual(response.data["meta"]["sync_status"], "synced")
        mock_push_plants_to_ai.assert_called_once()

    @patch("plants.views.push_plants_to_ai")
    def test_names_endpoint_fills_default_icon_and_growth_stages(self, mock_push_plants_to_ai):
        mock_push_plants_to_ai.return_value = []
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
        self.assertEqual(response.data["meta"]["flow_type"], "backend_owned_data")
        self.assertEqual(response.data["meta"]["source_type"], "db")
        self.assertEqual(response.data["meta"]["sync_status"], "synced")

    @patch("plants.views.push_plants_to_ai")
    def test_selected_endpoint_returns_farmer_products(self, mock_push_plants_to_ai):
        mock_push_plants_to_ai.return_value = []
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
        self.assertEqual(response.data["meta"]["ownership"], "backend")
        self.assertEqual(response.data["meta"]["sync_status"], "synced")

    @patch("plants.views.push_plants_to_ai")
    def test_list_exposes_backend_ownership_even_when_ai_sync_fails(self, mock_push_plants_to_ai):
        mock_push_plants_to_ai.side_effect = PlantSyncError("sync failed")
        Product.objects.create(farm_type=self.farm_type, name="Tomato", icon="leaf", growth_stages=["vegetative"])
        request = self.factory.get("/api/plants/")
        force_authenticate(request, user=self.user)

        response = PlantListView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["meta"]["flow_type"], "backend_owned_data_with_ai_enrichment")
        self.assertEqual(response.data["meta"]["sync_status"], "failed")

    def test_selected_endpoint_reads_seeded_backend_products_without_runtime_mock_data(self):
        tomato = Product.objects.create(farm_type=self.farm_type, name="Tomato", icon="leaf", growth_stages=["vegetative"])
        pepper = Product.objects.create(farm_type=self.farm_type, name="Pepper", icon="leaf", growth_stages=["flowering"])
        farm = FarmHub.objects.create(owner=self.user, farm_type=self.farm_type, name="seeded-farm")
        farm.products.add(tomato, pepper)

        request = self.factory.get(f"/api/plants/selected/?farm_uuid={farm.farm_uuid}")
        force_authenticate(request, user=self.user)

        with patch("plants.views.push_plants_to_ai", return_value=[]):
            response = SelectedPlantListView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertCountEqual([item["name"] for item in response.data["data"]], ["Tomato", "Pepper"])
        self.assertEqual(response.data["meta"]["source_type"], "db")
