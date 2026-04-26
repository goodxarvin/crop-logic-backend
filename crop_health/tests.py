from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import Resolver404, resolve
from rest_framework.test import APIRequestFactory, force_authenticate

from external_api_adapter.adapter import AdapterResponse
from farm_hub.models import FarmHub, FarmType
from unittest.mock import patch

from .views import CropHealthSummaryView, NdviHealthView


class NdviHealthViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            username="ndvi-user",
            password="secret123",
            email="ndvi@example.com",
            phone_number="09120000020",
        )
        self.other_user = get_user_model().objects.create_user(
            username="ndvi-other-user",
            password="secret123",
            email="ndvi-other@example.com",
            phone_number="09120000021",
        )
        self.farm_type = FarmType.objects.create(name="NDVI Farm Type")
        self.farm = FarmHub.objects.create(
            owner=self.user,
            farm_type=self.farm_type,
            name="NDVI Farm",
        )

    @patch("crop_health.views.external_api_request")
    def test_post_ndvi_health_returns_expected_payload(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={"data": {"result": {"ndviIndex": 0.78, "mean_ndvi": 0.78, "vegetation_health_class": "Healthy", "satellite_source": "sentinel-2"}}},
        )

        request = self.factory.post(
            "/api/crop-health/ndvi-health/",
            {"farm_uuid": str(self.farm.farm_uuid)},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = NdviHealthView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(response.data["msg"], "success")
        self.assertEqual(response.data["data"]["ndviIndex"], 0.78)
        self.assertEqual(response.data["data"]["mean_ndvi"], 0.78)
        self.assertEqual(response.data["data"]["vegetation_health_class"], "Healthy")
        self.assertEqual(response.data["data"]["satellite_source"], "sentinel-2")
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/soil-data/ndvi-health/",
            method="POST",
            payload={"farm_uuid": str(self.farm.farm_uuid)},
        )

    def test_post_ndvi_health_requires_farm_uuid(self):
        request = self.factory.post("/api/crop-health/ndvi-health/", {}, format="json")
        force_authenticate(request, user=self.user)

        response = NdviHealthView.as_view()(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("farm_uuid", response.data)

    def test_post_ndvi_health_returns_404_for_missing_farm(self):
        request = self.factory.post(
            "/api/crop-health/ndvi-health/",
            {"farm_uuid": "11111111-1111-1111-1111-111111111111"},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = NdviHealthView.as_view()(request)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["msg"], "Farm not found.")

    def test_post_ndvi_health_does_not_expose_other_users_farm(self):
        request = self.factory.post(
            "/api/crop-health/ndvi-health/",
            {"farm_uuid": str(self.farm.farm_uuid)},
            format="json",
        )
        force_authenticate(request, user=self.other_user)

        response = NdviHealthView.as_view()(request)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["msg"], "Farm not found.")

    def test_crop_health_routes_exist(self):
        self.assertIs(resolve("/api/crop-health/ndvi-health/").func.view_class, NdviHealthView)
        self.assertIs(resolve("/api/crop-health/summary/").func.view_class, CropHealthSummaryView)

    def test_removed_soil_health_alias_routes_no_longer_resolve(self):
        with self.assertRaises(Resolver404):
            resolve("/api/soil/health/ndvi-health/")
        with self.assertRaises(Resolver404):
            resolve("/api/soil/health/summary/")
        with self.assertRaises(Resolver404):
            resolve("/api/soil-data/ndvi-health/")
