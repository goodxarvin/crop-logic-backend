from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory

from external_api_adapter.adapter import AdapterResponse
from farm_hub.models import FarmHub, FarmType
from account.models import User

from .views import SoilAnomalyDetectionView, SoilMoistureHeatmapView, SoilSummaryView


TEST_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "soil-tests",
    }
}

TEST_SOIL_SUMMARY_CACHE_TTL = 14400
TEST_SOIL_ANOMALIES_CACHE_TTL = 14400


@override_settings(
    CACHES=TEST_CACHES,
    SOIL_ANOMALIES_CACHE_TTL=TEST_SOIL_ANOMALIES_CACHE_TTL,
)
class SoilAnomalyDetectionViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="soil-user",
            password="secret123",
            email="soil@example.com",
            phone_number="09120000100",
        )
        self.farm_type = FarmType.objects.create(name="Soil Farm Type")
        self.farm = FarmHub.objects.create(
            owner=self.user,
            farm_type=self.farm_type,
            name="Soil Farm",
        )

    @patch("soil.views.external_api_request")
    def test_anomalies_proxy_to_soile_anomaly_detection(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={
                "data": {
                    "farm_uuid": str(self.farm.farm_uuid),
                    "summary": "summary",
                    "explanation": "explanation",
                    "likely_cause": "cause",
                    "recommended_action": "action",
                    "monitoring_priority": "high",
                    "confidence": 0.91,
                    "generated_at": "2026-04-26T10:00:00Z",
                    "anomalies": [],
                    "interpretation": {},
                    "knowledge_base": None,
                    "raw_response": None,
                }
            },
        )

        request = self.factory.get(f"/api/soil/anomalies/?farm_uuid={self.farm.farm_uuid}")
        response = SoilAnomalyDetectionView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(response.data["data"]["monitoring_priority"], "high")
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/soile/anomaly-detection/",
            method="POST",
            payload={"farm_uuid": str(self.farm.farm_uuid)},
        )

    @patch("soil.views.external_api_request")
    def test_anomalies_cache_last_four_responses(self, mock_external_api_request):
        for index in range(5):
            farm = FarmHub.objects.create(owner=self.user, farm_type=self.farm_type, name=f"Soil Farm Cache {index}")
            mock_external_api_request.return_value = AdapterResponse(
                status_code=200,
                data={
                    "data": {
                        "farm_uuid": str(farm.farm_uuid),
                        "summary": f"summary {index}",
                        "anomalies": [],
                    }
                },
            )

            request = self.factory.get(f"/api/soil/anomalies/?farm_uuid={farm.farm_uuid}")
            response = SoilAnomalyDetectionView.as_view()(request)

            self.assertEqual(response.status_code, 200)

        cached_items = cache.get("soil:anomalies:recent")

        self.assertEqual(len(cached_items), 4)
        self.assertEqual(cached_items[0]["summary"], "summary 4")
        self.assertEqual(cached_items[-1]["summary"], "summary 1")

    @patch("soil.views.external_api_request")
    def test_anomalies_return_cached_response_for_same_farm(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={
                "data": {
                    "farm_uuid": str(self.farm.farm_uuid),
                    "summary": "cached summary",
                    "anomalies": [],
                }
            },
        )

        for _ in range(2):
            request = self.factory.get(f"/api/soil/anomalies/?farm_uuid={self.farm.farm_uuid}")
            response = SoilAnomalyDetectionView.as_view()(request)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data["data"]["summary"], "cached summary")

        self.assertEqual(cache.get(f"soil:anomalies:{self.farm.farm_uuid}")["summary"], "cached summary")
        mock_external_api_request.assert_called_once()

    @patch("soil.views.cache.set")
    @patch("soil.views.external_api_request")
    def test_anomalies_use_env_ttl_for_cache(self, mock_external_api_request, mock_cache_set):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={
                "data": {
                    "farm_uuid": str(self.farm.farm_uuid),
                    "summary": "summary",
                    "anomalies": [],
                }
            },
        )

        request = self.factory.get(f"/api/soil/anomalies/?farm_uuid={self.farm.farm_uuid}")
        response = SoilAnomalyDetectionView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(call.kwargs.get("timeout") == TEST_SOIL_ANOMALIES_CACHE_TTL for call in mock_cache_set.call_args_list))

    def test_anomalies_require_farm_uuid(self):
        request = self.factory.get("/api/soil/anomalies/")
        response = SoilAnomalyDetectionView.as_view()(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], 400)
        self.assertEqual(response.data["data"]["farm_uuid"][0], "This field is required.")

    def test_anomalies_return_404_for_missing_farm(self):
        request = self.factory.get("/api/soil/anomalies/?farm_uuid=11111111-1111-1111-1111-111111111111")
        response = SoilAnomalyDetectionView.as_view()(request)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["code"], 404)
        self.assertEqual(response.data["data"]["farm_uuid"][0], "Farm not found.")


class SoilMoistureHeatmapViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="soil-heatmap-user",
            password="secret123",
            email="soil-heatmap@example.com",
            phone_number="09120000101",
        )
        self.farm_type = FarmType.objects.create(name="Soil Heatmap Farm Type")
        self.farm = FarmHub.objects.create(
            owner=self.user,
            farm_type=self.farm_type,
            name="Heatmap Farm",
        )

    @patch("soil.views.external_api_request")
    def test_heatmap_proxies_to_soile_moisture_heatmap(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={
                "data": {
                    "farm_uuid": str(self.farm.farm_uuid),
                    "location": {},
                    "current_sensor": {},
                    "soil_profile": [],
                    "timestamp": "2026-04-26T10:00:00Z",
                    "grid_resolution": {},
                    "grid_cells": [],
                    "sensor_points": [],
                    "quality_legend": {},
                    "depth_layers": [],
                    "model_metadata": {},
                    "summary": {},
                }
            },
        )

        request = self.factory.get(f"/api/soil/moisture-heatmap/?farm_uuid={self.farm.farm_uuid}")
        response = SoilMoistureHeatmapView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(response.data["data"]["farm_uuid"], str(self.farm.farm_uuid))
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/soile/moisture-heatmap/",
            method="POST",
            payload={"farm_uuid": str(self.farm.farm_uuid)},
        )

    def test_heatmap_requires_farm_uuid(self):
        request = self.factory.get("/api/soil/moisture-heatmap/")
        response = SoilMoistureHeatmapView.as_view()(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], 400)
        self.assertEqual(response.data["data"]["farm_uuid"][0], "This field is required.")

    def test_heatmap_returns_404_for_missing_farm(self):
        request = self.factory.get("/api/soil/moisture-heatmap/?farm_uuid=11111111-1111-1111-1111-111111111111")
        response = SoilMoistureHeatmapView.as_view()(request)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["code"], 404)
        self.assertEqual(response.data["data"]["farm_uuid"][0], "Farm not found.")


@override_settings(
    CACHES=TEST_CACHES,
    SOIL_SUMMARY_CACHE_TTL=TEST_SOIL_SUMMARY_CACHE_TTL,
)
class SoilSummaryViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="soil-summary-user",
            password="secret123",
            email="soil-summary@example.com",
            phone_number="09120000102",
        )
        self.farm_type = FarmType.objects.create(name="Soil Summary Farm Type")
        self.farm = FarmHub.objects.create(
            owner=self.user,
            farm_type=self.farm_type,
            name="Summary Farm",
        )

    @patch("soil.views.external_api_request")
    def test_summary_proxies_to_soile_health_summary(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={
                "data": {
                    "farm_uuid": str(self.farm.farm_uuid),
                    "healthScore": 82,
                    "profileSource": "Tomato",
                    "healthScoreDetails": {},
                    "healthLanguage": {},
                    "avgSoilMoisture": 46,
                    "avgSoilMoistureRaw": 46.0,
                    "avgSoilMoistureStatus": "بهینه",
                }
            },
        )

        request = self.factory.get(f"/api/soil/summary/?farm_uuid={self.farm.farm_uuid}")
        response = SoilSummaryView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(response.data["data"]["healthScore"], 82)
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/soile/health-summary/",
            method="POST",
            payload={"farm_uuid": str(self.farm.farm_uuid)},
        )

    @patch("soil.views.external_api_request")
    def test_summary_returns_cached_response_for_same_farm(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={
                "data": {
                    "farm_uuid": str(self.farm.farm_uuid),
                    "healthScore": 82,
                    "profileSource": "Tomato",
                }
            },
        )

        for _ in range(2):
            request = self.factory.get(f"/api/soil/summary/?farm_uuid={self.farm.farm_uuid}")
            response = SoilSummaryView.as_view()(request)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data["data"]["healthScore"], 82)

        self.assertEqual(cache.get(f"soil:summary:{self.farm.farm_uuid}")["healthScore"], 82)
        mock_external_api_request.assert_called_once()

    @patch("soil.views.cache.set")
    @patch("soil.views.external_api_request")
    def test_summary_uses_env_ttl_for_cache(self, mock_external_api_request, mock_cache_set):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={
                "data": {
                    "farm_uuid": str(self.farm.farm_uuid),
                    "healthScore": 82,
                }
            },
        )

        request = self.factory.get(f"/api/soil/summary/?farm_uuid={self.farm.farm_uuid}")
        response = SoilSummaryView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(call.kwargs.get("timeout") == TEST_SOIL_SUMMARY_CACHE_TTL for call in mock_cache_set.call_args_list))

    @patch("soil.views.external_api_request")
    def test_summary_caches_last_four_responses(self, mock_external_api_request):
        for index in range(5):
            farm = FarmHub.objects.create(owner=self.user, farm_type=self.farm_type, name=f"Soil Summary Cache {index}")
            mock_external_api_request.return_value = AdapterResponse(
                status_code=200,
                data={
                    "data": {
                        "farm_uuid": str(farm.farm_uuid),
                        "healthScore": 80 + index,
                    }
                },
            )

            request = self.factory.get(f"/api/soil/summary/?farm_uuid={farm.farm_uuid}")
            response = SoilSummaryView.as_view()(request)

            self.assertEqual(response.status_code, 200)

        cached_items = cache.get("soil:summary:recent")
        self.assertEqual(len(cached_items), 4)
        self.assertEqual(cached_items[0]["healthScore"], 84)
        self.assertEqual(cached_items[-1]["healthScore"], 81)

    def test_summary_requires_farm_uuid(self):
        request = self.factory.get("/api/soil/summary/")
        response = SoilSummaryView.as_view()(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], 400)
        self.assertEqual(response.data["data"]["farm_uuid"][0], "This field is required.")

    def test_summary_returns_404_for_missing_farm(self):
        request = self.factory.get("/api/soil/summary/?farm_uuid=11111111-1111-1111-1111-111111111111")
        response = SoilSummaryView.as_view()(request)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["code"], 404)
        self.assertEqual(response.data["data"]["farm_uuid"][0], "Farm not found.")
