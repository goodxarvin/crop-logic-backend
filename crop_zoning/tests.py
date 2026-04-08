from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from kombu.exceptions import OperationalError
from rest_framework.test import APIRequestFactory, force_authenticate

from crop_zoning.models import CropArea, CropZone
from crop_zoning.views import (
    AreaView,
    CultivationRiskView,
    SoilQualityView,
    WaterNeedView,
    ZonesInitialView,
)
from farm_hub.models import FarmHub, FarmType


AREA_GEOJSON = {
    "type": "Feature",
    "properties": {},
    "geometry": {
        "type": "Polygon",
        "coordinates": [
            [
                [51.418934, 35.706815],
                [51.423054, 35.691062],
                [51.384258, 35.689389],
                [51.418934, 35.706815],
            ]
        ],
    },
}


@override_settings(
    USE_EXTERNAL_API_MOCK=True,
    CROP_ZONE_CHUNK_AREA_SQM=200000,
)
class ZonesInitialViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_post_accepts_area_geojson_alias(self):
        request = self.factory.post(
            "/api/crop-zoning/zones/initial/",
            {"area_geojson": AREA_GEOJSON},
            format="json",
        )

        response = ZonesInitialView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "success")
        self.assertGreater(response.data["data"]["zone_count"], 1)
        self.assertEqual(
            response.data["data"]["zone_count"],
            len(response.data["data"]["zones"]),
        )


@override_settings(
    USE_EXTERNAL_API_MOCK=True,
    CROP_ZONE_CHUNK_AREA_SQM=200000,
)
class AreaViewTests(TestCase):
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
        self.farm = FarmHub.objects.create(owner=self.user, name="farm-1", farm_type=self.farm_type)
        self.other_farm = FarmHub.objects.create(owner=self.other_user, name="farm-2", farm_type=self.farm_type)

    def _create_area(self, **kwargs):
        defaults = {
            "farm": self.farm,
            "geometry": AREA_GEOJSON,
            "points": AREA_GEOJSON["geometry"]["coordinates"][0][:-1],
            "center": {"longitude": 51.40874867, "latitude": 35.69575533},
            "area_sqm": 300000,
            "area_hectares": 30,
            "chunk_area_sqm": 200000,
            "zone_count": 2,
        }
        defaults.update(kwargs)
        return CropArea.objects.create(**defaults)

    def _request(self):
        request = self.factory.get(f"/api/crop-zoning/area/?farm_uuid={self.farm.farm_uuid}")
        force_authenticate(request, user=self.user)
        return request

    def _request_with_pagination(self, page=1, page_size=10):
        request = self.factory.get(
            f"/api/crop-zoning/area/?farm_uuid={self.farm.farm_uuid}&page={page}&page_size={page_size}"
        )
        force_authenticate(request, user=self.user)
        return request

    def test_get_requires_farm_uuid(self):
        request = self.factory.get("/api/crop-zoning/area/")
        force_authenticate(request, user=self.user)
        response = AreaView.as_view()(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["message"], "farm_uuid is required.")

    def test_get_rejects_foreign_farm_uuid(self):
        request = self.factory.get(f"/api/crop-zoning/area/?farm_uuid={self.other_farm.farm_uuid}")
        force_authenticate(request, user=self.user)

        response = AreaView.as_view()(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["message"], "Farm not found.")

    def test_get_returns_pending_task_status_until_all_zones_complete(self):
        crop_area = self._create_area()
        CropZone.objects.create(
            crop_area=crop_area,
            zone_id="zone-0",
            geometry=AREA_GEOJSON["geometry"],
            points=AREA_GEOJSON["geometry"]["coordinates"][0][:-1],
            center={"longitude": 51.4087, "latitude": 35.6957},
            area_sqm=200000,
            area_hectares=20,
            sequence=0,
            processing_status=CropZone.STATUS_PENDING,
            task_id="celery-task-1",
        )
        CropZone.objects.create(
            crop_area=crop_area,
            zone_id="zone-1",
            geometry=AREA_GEOJSON["geometry"],
            points=AREA_GEOJSON["geometry"]["coordinates"][0][:-1],
            center={"longitude": 51.4088, "latitude": 35.6958},
            area_sqm=100000,
            area_hectares=10,
            sequence=1,
            processing_status=CropZone.STATUS_PROCESSING,
            task_id="celery-task-1",
        )

        response = AreaView.as_view()(self._request())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["data"]["task"]["status"], "PROCESSING")
        self.assertEqual(response.data["data"]["task"]["total_zones"], 2)
        self.assertEqual(response.data["data"]["area"], AREA_GEOJSON)
        self.assertEqual(len(response.data["data"]["zones"]), 2)
        self.assertEqual(response.data["data"]["zones"][0]["zoneId"], "zone-0")
        self.assertIn("processing_status", response.data["data"]["zones"][0])

    def test_get_returns_area_when_all_tasks_complete(self):
        crop_area = self._create_area()
        for sequence in range(2):
            CropZone.objects.create(
                crop_area=crop_area,
                zone_id=f"zone-{sequence}",
                geometry=AREA_GEOJSON["geometry"],
                points=AREA_GEOJSON["geometry"]["coordinates"][0][:-1],
                center={"longitude": 51.4087 + (sequence * 0.0001), "latitude": 35.6957},
                area_sqm=150000,
                area_hectares=15,
                sequence=sequence,
                processing_status=CropZone.STATUS_COMPLETED,
                task_id="celery-task-1",
            )

        response = AreaView.as_view()(self._request())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["task"]["status"], "SUCCESS")
        self.assertEqual(response.data["data"]["area"], AREA_GEOJSON)
        self.assertEqual(len(response.data["data"]["zones"]), 2)
        self.assertEqual(response.data["data"]["zones"][1]["zoneId"], "zone-1")
        self.assertIn("crop", response.data["data"]["zones"][0])
        self.assertIn("waterNeedLayer", response.data["data"]["zones"][0])

    def test_get_returns_paginated_zones(self):
        crop_area = self._create_area(zone_count=3, area_sqm=300000, area_hectares=30)
        for sequence in range(3):
            CropZone.objects.create(
                crop_area=crop_area,
                zone_id=f"zone-{sequence}",
                geometry=AREA_GEOJSON["geometry"],
                points=AREA_GEOJSON["geometry"]["coordinates"][0][:-1],
                center={"longitude": 51.4087 + (sequence * 0.0001), "latitude": 35.6957},
                area_sqm=100000,
                area_hectares=10,
                sequence=sequence,
                processing_status=CropZone.STATUS_COMPLETED,
                task_id=f"celery-task-{sequence}",
            )

        response = AreaView.as_view()(self._request_with_pagination(page=2, page_size=1))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]["zones"]), 1)
        self.assertEqual(response.data["data"]["zones"][0]["zoneId"], "zone-1")
        self.assertEqual(response.data["data"]["pagination"]["page"], 2)
        self.assertEqual(response.data["data"]["pagination"]["page_size"], 1)
        self.assertEqual(response.data["data"]["pagination"]["total_pages"], 3)
        self.assertTrue(response.data["data"]["pagination"]["has_next"])
        self.assertTrue(response.data["data"]["pagination"]["has_previous"])

    def test_get_rejects_invalid_pagination_params(self):
        response = AreaView.as_view()(self._request_with_pagination(page=0, page_size=10))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["message"], "page must be a positive integer.")

    @patch("crop_zoning.services.dispatch_zone_processing_tasks")
    def test_get_dispatches_zone_task_when_task_id_is_missing(self, mock_dispatch):
        crop_area = self._create_area(zone_count=1, area_sqm=200000, area_hectares=20)
        CropZone.objects.create(
            crop_area=crop_area,
            zone_id="zone-0",
            geometry=AREA_GEOJSON["geometry"],
            points=AREA_GEOJSON["geometry"]["coordinates"][0][:-1],
            center={"longitude": 51.4087, "latitude": 35.6957},
            area_sqm=200000,
            area_hectares=20,
            sequence=0,
            processing_status=CropZone.STATUS_PENDING,
            task_id="",
        )

        response = AreaView.as_view()(self._request())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "success")
        mock_dispatch.assert_called_once()

    @patch("crop_zoning.services.create_zones_and_dispatch")
    def test_get_creates_area_when_farm_has_no_data(self, mock_create):
        created_area = self._create_area(zone_count=0)
        mock_create.return_value = (created_area, [])

        response = AreaView.as_view()(self._request())

        self.assertEqual(response.status_code, 200)
        mock_create.assert_called_once()
        self.assertEqual(mock_create.call_args.kwargs["farm"], self.farm)

    @patch("crop_zoning.tasks.process_zone_soil_data.delay")
    def test_each_zone_gets_its_own_task(self, mock_delay):
        crop_area = self._create_area()
        zone0 = CropZone.objects.create(
            crop_area=crop_area,
            zone_id="zone-0",
            geometry=AREA_GEOJSON["geometry"],
            points=AREA_GEOJSON["geometry"]["coordinates"][0][:-1],
            center={"longitude": 51.4087, "latitude": 35.6957},
            area_sqm=200000,
            area_hectares=20,
            sequence=0,
            processing_status=CropZone.STATUS_PENDING,
            task_id="",
        )
        zone1 = CropZone.objects.create(
            crop_area=crop_area,
            zone_id="zone-1",
            geometry=AREA_GEOJSON["geometry"],
            points=AREA_GEOJSON["geometry"]["coordinates"][0][:-1],
            center={"longitude": 51.4088, "latitude": 35.6958},
            area_sqm=100000,
            area_hectares=10,
            sequence=1,
            processing_status=CropZone.STATUS_PENDING,
            task_id="",
        )

        response = AreaView.as_view()(self._request())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_delay.call_count, 2)
        zone0.refresh_from_db()
        zone1.refresh_from_db()
        self.assertTrue(zone0.task_id)
        self.assertTrue(zone1.task_id)
        self.assertNotEqual(zone0.task_id, zone1.task_id)

    @patch("crop_zoning.services.AsyncResult")
    def test_stale_tasks_are_redispatched(self, mock_async_result):
        crop_area = self._create_area()
        stale_time = timezone.now() - timedelta(minutes=10)
        stale_zone = CropZone.objects.create(
            crop_area=crop_area,
            zone_id="zone-0",
            geometry=AREA_GEOJSON["geometry"],
            points=AREA_GEOJSON["geometry"]["coordinates"][0][:-1],
            center={"longitude": 51.4087, "latitude": 35.6957},
            area_sqm=200000,
            area_hectares=20,
            sequence=0,
            processing_status=CropZone.STATUS_PROCESSING,
            task_id="stale-task",
        )
        CropZone.objects.filter(id=stale_zone.id).update(updated_at=stale_time)

        mock_async_result.side_effect = OperationalError("broker down")

        with patch("crop_zoning.services.dispatch_zone_processing_tasks") as mock_dispatch:
            response = AreaView.as_view()(self._request())

        self.assertEqual(response.status_code, 200)
        mock_dispatch.assert_called_once_with(zone_ids=[stale_zone.id], force=True)


@override_settings(
    USE_EXTERNAL_API_MOCK=True,
    CROP_ZONE_CHUNK_AREA_SQM=200000,
)
class LayerAreaViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            username="layer-farmer",
            password="secret123",
            email="layer@example.com",
            phone_number="09120000002",
        )
        self.farm_type = FarmType.objects.create(name="باغی")
        self.farm = FarmHub.objects.create(owner=self.user, name="layer-farm", farm_type=self.farm_type)

    def _create_area(self, **kwargs):
        defaults = {
            "farm": self.farm,
            "geometry": AREA_GEOJSON,
            "points": AREA_GEOJSON["geometry"]["coordinates"][0][:-1],
            "center": {"longitude": 51.40874867, "latitude": 35.69575533},
            "area_sqm": 300000,
            "area_hectares": 30,
            "chunk_area_sqm": 200000,
            "zone_count": 1,
        }
        defaults.update(kwargs)
        return CropArea.objects.create(**defaults)

    def _create_completed_zone(self):
        crop_area = self._create_area()
        CropZone.objects.create(
            crop_area=crop_area,
            zone_id="zone-0",
            geometry=AREA_GEOJSON["geometry"],
            points=AREA_GEOJSON["geometry"]["coordinates"][0][:-1],
            center={"longitude": 51.4087, "latitude": 35.6957},
            area_sqm=300000,
            area_hectares=30,
            sequence=0,
            processing_status=CropZone.STATUS_COMPLETED,
            task_id="celery-task-1",
        )
        return crop_area

    def _request(self, path):
        request = self.factory.get(f"{path}?farm_uuid={self.farm.farm_uuid}")
        force_authenticate(request, user=self.user)
        return request

    def test_water_need_view_requires_farm_uuid(self):
        request = self.factory.get("/api/crop-zoning/water-need/")
        force_authenticate(request, user=self.user)

        response = WaterNeedView.as_view()(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["message"], "farm_uuid is required.")

    def test_water_need_view_returns_area_style_payload(self):
        self._create_completed_zone()

        response = WaterNeedView.as_view()(self._request("/api/crop-zoning/water-need/"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["task"]["status"], "SUCCESS")
        self.assertEqual(response.data["data"]["area"], AREA_GEOJSON)
        self.assertEqual(len(response.data["data"]["zones"]), 1)
        self.assertIn("waterNeedLayer", response.data["data"]["zones"][0])
        self.assertNotIn("soilQualityLayer", response.data["data"]["zones"][0])
        self.assertNotIn("cultivationRiskLayer", response.data["data"]["zones"][0])

    def test_soil_quality_view_returns_area_style_payload(self):
        self._create_completed_zone()

        response = SoilQualityView.as_view()(self._request("/api/crop-zoning/soil-quality/"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["task"]["status"], "SUCCESS")
        self.assertEqual(len(response.data["data"]["zones"]), 1)
        self.assertIn("soilQualityLayer", response.data["data"]["zones"][0])
        self.assertNotIn("waterNeedLayer", response.data["data"]["zones"][0])
        self.assertNotIn("cultivationRiskLayer", response.data["data"]["zones"][0])

    def test_cultivation_risk_view_returns_area_style_payload(self):
        self._create_completed_zone()

        response = CultivationRiskView.as_view()(self._request("/api/crop-zoning/cultivation-risk/"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["task"]["status"], "SUCCESS")
        self.assertEqual(len(response.data["data"]["zones"]), 1)
        self.assertIn("cultivationRiskLayer", response.data["data"]["zones"][0])
        self.assertNotIn("waterNeedLayer", response.data["data"]["zones"][0])
        self.assertNotIn("soilQualityLayer", response.data["data"]["zones"][0])
