from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory

from crop_zoning.models import CropArea, CropZone, CropZoneAnalysis
from device_hub.models import DeviceCatalog, FarmDevice, SensorExternalRequestLog
from external_api_adapter.adapter import AdapterResponse
from farm_hub.models import FarmHub, FarmType
from account.models import User

from .views import SoilAnomalyDetectionView, SoilMoistureHeatmapView, SoilMonitorView, SoilSummaryView


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

    def test_heatmap_returns_only_existing_zone_clusters_with_moisture(self):
        area = CropArea.objects.create(
            farm=self.farm,
            geometry={"type": "Polygon", "coordinates": []},
            points=[],
            center={"lat": 35.7, "lon": 51.4},
            area_sqm=2000,
            area_hectares=0.2,
            chunk_area_sqm=1000,
            zone_count=2,
        )
        self.farm.current_crop_area = area
        self.farm.save(update_fields=["current_crop_area", "updated_at"])

        zone_one = CropZone.objects.create(
            crop_area=area,
            zone_id="cluster-a",
            geometry={"type": "Polygon", "coordinates": []},
            points=[],
            center={"lat": 35.71, "lon": 51.41},
            area_sqm=1000,
            area_hectares=0.1,
            sequence=1,
        )
        zone_two = CropZone.objects.create(
            crop_area=area,
            zone_id="cluster-b",
            geometry={"type": "Polygon", "coordinates": []},
            points=[],
            center={"lat": 35.72, "lon": 51.42},
            area_sqm=1000,
            area_hectares=0.1,
            sequence=2,
        )

        catalog = DeviceCatalog.objects.create(code="soil_probe_heatmap", name="Soil Probe Heatmap")
        sensor_one = FarmDevice.objects.create(
            farm=self.farm,
            sensor_catalog=catalog,
            physical_device_uuid="44444444-4444-4444-4444-444444444444",
            name="Cluster A Sensor",
            sensor_type="soil_probe",
            cluster_uuid=zone_one.uuid,
        )
        sensor_two = FarmDevice.objects.create(
            farm=self.farm,
            sensor_catalog=catalog,
            physical_device_uuid="55555555-5555-5555-5555-555555555555",
            name="Cluster B Sensor",
            sensor_type="soil_probe",
            cluster_uuid=zone_two.uuid,
        )
        SensorExternalRequestLog.objects.create(
            farm_uuid=self.farm.farm_uuid,
            sensor_catalog_uuid=catalog.uuid,
            physical_device_uuid=sensor_one.physical_device_uuid,
            cluster_uuid=zone_one.uuid,
            payload={"soil_moisture": 41.0},
        )
        SensorExternalRequestLog.objects.create(
            farm_uuid=self.farm.farm_uuid,
            sensor_catalog_uuid=catalog.uuid,
            physical_device_uuid=sensor_two.physical_device_uuid,
            cluster_uuid=zone_two.uuid,
            payload={"soil_moisture": 67.0},
        )

        request = self.factory.get(f"/api/soil/moisture-heatmap/?farm_uuid={self.farm.farm_uuid}")
        response = SoilMoistureHeatmapView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(response.data["data"]["farm_uuid"], str(self.farm.farm_uuid))
        self.assertEqual(len(response.data["data"]["grid_cells"]), 2)
        self.assertEqual(response.data["data"]["grid_cells"][0]["cluster"], "cluster-a")
        self.assertEqual(response.data["data"]["grid_cells"][0]["moisture"], 41.0)
        self.assertEqual(response.data["data"]["grid_cells"][1]["cluster"], "cluster-b")
        self.assertEqual(response.data["data"]["grid_cells"][1]["moisture"], 67.0)
        self.assertEqual(response.data["data"]["summary"]["total_clusters"], 2)

    @patch("soil.services.ensure_farm_ai_clusters_synced")
    def test_heatmap_fetches_clusters_from_ai_when_backend_has_no_zone_data(self, mock_sync_clusters):
        def _seed_ai_clusters(*args, **kwargs):
            area = CropArea.objects.create(
                farm=self.farm,
                geometry={"type": "Polygon", "coordinates": []},
                points=[],
                center={"lat": 35.7, "lon": 51.4},
                area_sqm=2000,
                area_hectares=0.2,
                chunk_area_sqm=1000,
                zone_count=2,
            )
            self.farm.current_crop_area = area
            self.farm.save(update_fields=["current_crop_area", "updated_at"])

            zone_one = CropZone.objects.create(
                crop_area=area,
                zone_id="cluster-a",
                geometry={"type": "Polygon", "coordinates": []},
                points=[],
                center={"lat": 35.71, "lon": 51.41},
                area_sqm=1000,
                area_hectares=0.1,
                sequence=1,
            )
            zone_two = CropZone.objects.create(
                crop_area=area,
                zone_id="cluster-b",
                geometry={"type": "Polygon", "coordinates": []},
                points=[],
                center={"lat": 35.72, "lon": 51.42},
                area_sqm=1000,
                area_hectares=0.1,
                sequence=2,
            )
            CropZoneAnalysis.objects.create(
                crop_zone=zone_one,
                source="ai_location_data",
                external_record_id="cluster-a",
                raw_response={
                    "cluster_recommendation": {
                        "satellite_metrics": {"soil_vv": 0.31},
                        "resolved_metrics": {"soil_moisture": 44.0},
                    }
                },
                depths=[],
            )
            CropZoneAnalysis.objects.create(
                crop_zone=zone_two,
                source="ai_location_data",
                external_record_id="cluster-b",
                raw_response={
                    "cluster_recommendation": {
                        "satellite_metrics": {"soil_vv": 0.52},
                        "resolved_metrics": {"soil_moisture": 61.0},
                    }
                },
                depths=[],
            )
            return area

        mock_sync_clusters.side_effect = _seed_ai_clusters

        request = self.factory.get(f"/api/soil/moisture-heatmap/?farm_uuid={self.farm.farm_uuid}")
        response = SoilMoistureHeatmapView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(len(response.data["data"]["grid_cells"]), 2)
        self.assertEqual(response.data["data"]["grid_cells"][0]["soil_vv"], 0.31)
        self.assertEqual(response.data["data"]["grid_cells"][0]["moisture"], 44.0)
        self.assertEqual(response.data["data"]["grid_cells"][1]["soil_vv"], 0.52)
        self.assertEqual(response.data["data"]["summary"]["monitored_clusters"], 2)
        mock_sync_clusters.assert_called_once_with(farm_uuid=self.farm.farm_uuid, owner=self.farm.owner)

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


class SoilMonitorViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="soil-monitor-user",
            password="secret123",
            email="soil-monitor@example.com",
            phone_number="09120000103",
        )
        self.farm_type = FarmType.objects.create(name="Soil Monitor Farm Type")
        self.farm = FarmHub.objects.create(
            owner=self.user,
            farm_type=self.farm_type,
            name="Monitor Farm",
        )

    def test_monitor_returns_zone_sensor_data_from_crop_zoning_and_device_logs(self):
        area = CropArea.objects.create(
            farm=self.farm,
            geometry={"type": "Polygon", "coordinates": []},
            points=[],
            center={"lat": 35.7, "lon": 51.4},
            area_sqm=2000,
            area_hectares=0.2,
            chunk_area_sqm=1000,
            zone_count=1,
        )
        self.farm.current_crop_area = area
        self.farm.save(update_fields=["current_crop_area", "updated_at"])

        zone_cluster_uuid = "11111111-1111-1111-1111-111111111222"
        CropZone.objects.create(
            crop_area=area,
            zone_id=zone_cluster_uuid,
            geometry={"type": "Polygon", "coordinates": []},
            points=[],
            center={"lat": 35.71, "lon": 51.41},
            area_sqm=1000,
            area_hectares=0.1,
            sequence=1,
        )

        catalog = DeviceCatalog.objects.create(code="soil_probe", name="Soil Probe")
        sensor = FarmDevice.objects.create(
            farm=self.farm,
            sensor_catalog=catalog,
            physical_device_uuid="33333333-3333-3333-3333-333333333333",
            name="Zone A Sensor",
            sensor_type="soil_probe",
            cluster_uuid=zone_cluster_uuid,
        )
        SensorExternalRequestLog.objects.create(
            farm_uuid=self.farm.farm_uuid,
            sensor_catalog_uuid=catalog.uuid,
            physical_device_uuid=sensor.physical_device_uuid,
            cluster_uuid=zone_cluster_uuid,
            payload={"soil_moisture": 43.5, "temperature": 24.2, "ph": 6.8},
        )

        request = self.factory.get(f"/api/soil/monitor/?farm_uuid={self.farm.farm_uuid}")
        response = SoilMonitorView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(response.data["data"]["zone_count"], 1)
        self.assertEqual(response.data["data"]["monitored_zones"], 1)
        zone_data = response.data["data"]["zones"][0]
        self.assertEqual(zone_data["zone_id"], zone_cluster_uuid)
        self.assertEqual(zone_data["aggregated_metrics"]["soil_moisture"], 43.5)
        self.assertEqual(zone_data["status"]["label"], "کم")
        self.assertEqual(len(zone_data["sensors"]), 1)
        self.assertEqual(zone_data["sensors"][0]["name"], "Zone A Sensor")

    def test_monitor_requires_farm_uuid(self):
        request = self.factory.get("/api/soil/monitor/")
        response = SoilMonitorView.as_view()(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], 400)
        self.assertEqual(response.data["data"]["farm_uuid"][0], "This field is required.")

    def test_monitor_returns_404_for_missing_farm(self):
        request = self.factory.get("/api/soil/monitor/?farm_uuid=11111111-1111-1111-1111-111111111111")
        response = SoilMonitorView.as_view()(request)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["code"], 404)
        self.assertEqual(response.data["data"]["farm_uuid"][0], "Farm not found.")
