from unittest.mock import patch

from kombu.exceptions import OperationalError

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIRequestFactory
from datetime import timedelta

from crop_zoning.models import CropArea, CropZone
from crop_zoning.views import AreaView, ZonesInitialView
from sensor_hub.models import Sensor


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
        self.sensor = Sensor.objects.create(owner=self.user, name="sensor-1")

    def _create_area(self, **kwargs):
        defaults = {
            "sensor": self.sensor,
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
        return self.factory.get(f"/api/crop-zoning/area/?sensor_uuid={self.sensor.uuid_sensor}")

    def _request_with_pagination(self, page=1, page_size=10):
        return self.factory.get(
            f"/api/crop-zoning/area/?sensor_uuid={self.sensor.uuid_sensor}&page={page}&page_size={page_size}"
        )

    def test_get_requires_sensor_uuid(self):
        request = self.factory.get("/api/crop-zoning/area/")
        response = AreaView.as_view()(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["message"], "sensor_uuid is required.")

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
    def test_get_creates_area_when_sensor_has_no_data(self, mock_create):
        created_area = self._create_area(zone_count=0)
        mock_create.return_value = (created_area, [])

        response = AreaView.as_view()(self._request())

        self.assertEqual(response.status_code, 200)
        mock_create.assert_called_once()
        self.assertEqual(mock_create.call_args.kwargs["sensor"], self.sensor)

    @patch("crop_zoning.tasks.process_zone_soil_data.delay")
    def test_each_zone_gets_its_own_task(self, mock_delay):
        crop_area = self._create_area()
        zone0 = CropZone.objects.create(
            crop_area=crop_area,
            zone_id="zone-0",
            geometry=AREA_GEOJSON["geometry"],
            points=AREA_GEOJSON["geometry"]["coordinates"][0][:-1],
            center={"longitude": 51.4087, "latitude": 35.6957},
            area_sqm=150000,
            area_hectares=15,
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
            area_sqm=150000,
            area_hectares=15,
            sequence=1,
            processing_status=CropZone.STATUS_PENDING,
            task_id="",
        )

        class Result:
            def __init__(self, task_id):
                self.id = task_id

        mock_delay.side_effect = [Result("task-zone-0"), Result("task-zone-1")]

        response = AreaView.as_view()(self._request())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_delay.call_count, 2)
        zone0.refresh_from_db()
        zone1.refresh_from_db()
        self.assertEqual(zone0.task_id, "task-zone-0")
        self.assertEqual(zone1.task_id, "task-zone-1")

    @patch("crop_zoning.tasks.process_zone_soil_data.delay", side_effect=OperationalError("redis down"))
    def test_get_generates_local_task_id_when_broker_is_unavailable(self, mock_delay):
        crop_area = self._create_area(zone_count=1, area_sqm=200000, area_hectares=20)
        zone = CropZone.objects.create(
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
        zone.refresh_from_db()
        self.assertTrue(zone.task_id)
        self.assertEqual(response.data["data"]["task"]["summary"]["remaining"], 1)
        self.assertEqual(response.data["data"]["task"]["remaining_zones"], 1)
        self.assertEqual(response.data["data"]["task"]["status"], "PENDING")
        self.assertIn("Celery broker unavailable", zone.processing_error)

    @patch("crop_zoning.tasks.process_zone_soil_data.delay")
    def test_get_stores_task_id_and_reuses_it_on_next_request(self, mock_delay):
        crop_area = self._create_area(zone_count=1, area_sqm=200000, area_hectares=20)
        zone = CropZone.objects.create(
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

        class Result:
            id = "persisted-task-id"

        mock_delay.return_value = Result()

        first_response = AreaView.as_view()(self._request())
        self.assertEqual(first_response.status_code, 200)
        zone.refresh_from_db()
        self.assertEqual(zone.task_id, "persisted-task-id")
        self.assertEqual(first_response.data["data"]["task"]["summary"]["done"], 0)
        self.assertEqual(first_response.data["data"]["task"]["summary"]["remaining"], 1)
        self.assertEqual(mock_delay.call_count, 1)

        second_response = AreaView.as_view()(self._request())
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(second_response.data["data"]["task"]["summary"]["remaining"], 1)
        self.assertEqual(second_response.data["data"]["task"]["status"], "PENDING")
        self.assertEqual(mock_delay.call_count, 1)

    @patch("crop_zoning.services.AsyncResult")
    @patch("crop_zoning.tasks.process_zone_soil_data.delay")
    def test_get_redispatches_pending_zone_when_shared_task_already_completed(self, mock_delay, mock_async_result):
        crop_area = self._create_area()
        CropZone.objects.create(
            crop_area=crop_area,
            zone_id="zone-0",
            geometry=AREA_GEOJSON["geometry"],
            points=AREA_GEOJSON["geometry"]["coordinates"][0][:-1],
            center={"longitude": 51.4087, "latitude": 35.6957},
            area_sqm=150000,
            area_hectares=15,
            sequence=0,
            processing_status=CropZone.STATUS_COMPLETED,
            task_id="legacy-shared-task-id",
        )
        stale_zone = CropZone.objects.create(
            crop_area=crop_area,
            zone_id="zone-1",
            geometry=AREA_GEOJSON["geometry"],
            points=AREA_GEOJSON["geometry"]["coordinates"][0][:-1],
            center={"longitude": 51.4088, "latitude": 35.6958},
            area_sqm=150000,
            area_hectares=15,
            sequence=1,
            processing_status=CropZone.STATUS_PENDING,
            task_id="legacy-shared-task-id",
        )
        stale_zone.updated_at = timezone.now() - timedelta(minutes=10)
        stale_zone.save(update_fields=["updated_at"])

        class Result:
            id = "requeued-zone-1"

        mock_delay.return_value = Result()
        mock_async_result.return_value.state = "SUCCESS"

        response = AreaView.as_view()(self._request())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_delay.call_count, 1)
        stale_zone.refresh_from_db()
        self.assertEqual(stale_zone.task_id, "requeued-zone-1")
