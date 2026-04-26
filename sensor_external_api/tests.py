from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory
from unittest.mock import patch

from external_api_adapter.adapter import AdapterResponse
from external_api_adapter.exceptions import ExternalAPIRequestError
from crop_zoning.models import CropArea
from farm_hub.models import FarmHub, FarmSensor, FarmType
from notifications.models import FarmNotification
from sensor_catalog.models import SensorCatalog

from .models import SensorExternalRequestLog
from .services import get_latest_sensor_external_request_log
from .views import SensorExternalAPIView, SensorExternalRequestLogListAPIView


@override_settings(
    SENSOR_EXTERNAL_API_KEY="12345",
    FARM_DATA_API_KEY="farm-data-key",
)
class SensorExternalAPIViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            username="sensor-external-user",
            password="secret123",
            email="sensor-external@example.com",
            phone_number="09120000015",
        )
        self.farm_type = FarmType.objects.create(name="سنسور خارجی")
        self.farm = FarmHub.objects.create(
            owner=self.user,
            farm_type=self.farm_type,
            name="Farm External",
        )
        self.sensor_catalog = SensorCatalog.objects.create(
            code="ext-sensor-v1",
            name="External Sensor",
        )
        self.crop_area = CropArea.objects.create(
            farm=self.farm,
            geometry={
                "type": "Polygon",
                "coordinates": [
                    [
                        [51.39, 35.7],
                        [51.41, 35.7],
                        [51.41, 35.72],
                        [51.39, 35.72],
                        [51.39, 35.7],
                    ]
                ],
            },
            points=[
                [51.39, 35.7],
                [51.41, 35.7],
                [51.41, 35.72],
                [51.39, 35.72],
            ],
            center={"lat": 35.71, "lng": 51.4},
            area_sqm=1000,
            area_hectares=0.1,
            chunk_area_sqm=1000,
        )
        self.farm.current_crop_area = self.crop_area
        self.farm.save(update_fields=["current_crop_area"])
        self.sensor = FarmSensor.objects.create(
            farm=self.farm,
            sensor_catalog=self.sensor_catalog,
            physical_device_uuid="11111111-1111-1111-1111-111111111111",
            name="sensor-7-1",
            sensor_type="weather_station",
        )

    def test_requires_api_key(self):
        request = self.factory.post(
            "/api/sensor-external-api/",
            {"uuid": str(self.sensor.physical_device_uuid), "payload": {"temp": 12}},
            format="json",
        )

        response = SensorExternalAPIView.as_view()(request)

        self.assertEqual(response.status_code, 401)

    @patch("sensor_external_api.services.external_api_request")
    def test_creates_notification_and_request_log_for_device_uuid(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(status_code=201, data={})
        request = self.factory.post(
            "/api/sensor-external-api/",
            {"uuid": str(self.sensor.physical_device_uuid), "payload": {"temp": 12}},
            format="json",
            HTTP_X_API_KEY="12345",
        )

        response = SensorExternalAPIView.as_view()(request)

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            FarmNotification.objects.filter(
                farm=self.farm,
                title="Sensor external API request",
            ).exists()
        )
        self.assertTrue(
            SensorExternalRequestLog.objects.filter(
                farm_uuid=self.farm.farm_uuid,
                sensor_catalog_uuid=self.sensor_catalog.uuid,
                physical_device_uuid=self.sensor.physical_device_uuid,
                payload={"temp": 12},
            ).exists()
        )
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/farm-data/",
            method="POST",
            payload={
                "farm_uuid": str(self.farm.farm_uuid),
                "farm_boundary": self.crop_area.geometry,
                "sensor_payload": {
                    "sensor-7-1": {"temp": 12},
                },
            },
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-API-Key": "farm-data-key",
                "Authorization": "Api-Key farm-data-key",
            },
        )

    def test_returns_404_for_unknown_device_uuid(self):
        request = self.factory.post(
            "/api/sensor-external-api/",
            {"uuid": "22222222-2222-2222-2222-222222222222", "payload": {"temp": 12}},
            format="json",
            HTTP_X_API_KEY="12345",
        )

        response = SensorExternalAPIView.as_view()(request)

        self.assertEqual(response.status_code, 404)

    @patch("sensor_external_api.services.external_api_request")
    def test_returns_503_when_farm_data_api_is_unavailable(self, mock_external_api_request):
        mock_external_api_request.side_effect = ExternalAPIRequestError("connection error")

        request = self.factory.post(
            "/api/sensor-external-api/",
            {"uuid": str(self.sensor.physical_device_uuid), "payload": {"temp": 12}},
            format="json",
            HTTP_X_API_KEY="12345",
        )

        response = SensorExternalAPIView.as_view()(request)

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data["code"], 503)
        self.assertIn("Farm data API request failed", response.data["msg"])


class SensorExternalServiceTests(TestCase):
    def test_get_latest_sensor_external_request_log_returns_latest_matching_record(self):
        first_log = SensorExternalRequestLog.objects.create(
            farm_uuid="11111111-1111-1111-1111-111111111111",
            sensor_catalog_uuid="22222222-2222-2222-2222-222222222222",
            physical_device_uuid="33333333-3333-3333-3333-333333333333",
            payload={"temp": 12},
        )
        latest_log = SensorExternalRequestLog.objects.create(
            farm_uuid=first_log.farm_uuid,
            sensor_catalog_uuid=first_log.sensor_catalog_uuid,
            physical_device_uuid=first_log.physical_device_uuid,
            payload={"temp": 18},
        )
        SensorExternalRequestLog.objects.create(
            farm_uuid=first_log.farm_uuid,
            sensor_catalog_uuid=first_log.sensor_catalog_uuid,
            physical_device_uuid="44444444-4444-4444-4444-444444444444",
            payload={"temp": 25},
        )

        log = get_latest_sensor_external_request_log(
            farm_uuid=first_log.farm_uuid,
            sensor_catalog_uuid=first_log.sensor_catalog_uuid,
            physical_device_uuid=first_log.physical_device_uuid,
        )

        self.assertIsNotNone(log)
        self.assertEqual(log.id, latest_log.id)
        self.assertEqual(log.payload, {"temp": 18})


@override_settings(SENSOR_EXTERNAL_API_KEY="12345")
class SensorExternalRequestLogListAPIViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            username="sensor-external-log-user",
            password="secret123",
            email="sensor-external-log@example.com",
            phone_number="09120000016",
        )
        self.farm_type = FarmType.objects.create(name="لاگ سنسور خارجی")
        self.farm = FarmHub.objects.create(
            owner=self.user,
            farm_type=self.farm_type,
            name="Farm Log External",
            farm_uuid="11111111-1111-1111-1111-111111111111",
        )
        self.farm_uuid = self.farm.farm_uuid
        self.other_farm_uuid = "aaaaaaaa-1111-1111-1111-111111111111"
        self.first_catalog = SensorCatalog.objects.create(
            code="ext-sensor-log-1",
            name="External Sensor Log 1",
            description="Sensor catalog for first log",
            returned_data_fields=["temp"],
        )
        self.second_catalog = SensorCatalog.objects.create(
            code="ext-sensor-log-2",
            name="External Sensor Log 2",
            description="Sensor catalog for second log",
            returned_data_fields=["humidity"],
        )
        self.first_sensor = FarmSensor.objects.create(
            farm=self.farm,
            sensor_catalog=self.first_catalog,
            physical_device_uuid="33333333-3333-3333-3333-333333333333",
            name="External device 1",
            sensor_type="weather_station",
            specifications={"model": "FH-1"},
            power_source={"type": "battery"},
        )
        self.second_sensor = FarmSensor.objects.create(
            farm=self.farm,
            sensor_catalog=self.second_catalog,
            physical_device_uuid="55555555-5555-5555-5555-555555555555",
            name="External device 2",
            sensor_type="soil_sensor",
            specifications={"model": "FH-2"},
            power_source={"type": "solar"},
        )

        self.first_log = SensorExternalRequestLog.objects.create(
            farm_uuid=self.farm_uuid,
            sensor_catalog_uuid=self.first_catalog.uuid,
            physical_device_uuid=self.first_sensor.physical_device_uuid,
            payload={"temp": 12},
        )
        self.second_log = SensorExternalRequestLog.objects.create(
            farm_uuid=self.farm_uuid,
            sensor_catalog_uuid=self.second_catalog.uuid,
            physical_device_uuid=self.second_sensor.physical_device_uuid,
            payload={"temp": 18},
        )
        SensorExternalRequestLog.objects.create(
            farm_uuid=self.other_farm_uuid,
            sensor_catalog_uuid="66666666-6666-6666-6666-666666666666",
            physical_device_uuid="77777777-7777-7777-7777-777777777777",
            payload={"temp": 24},
        )

    def test_requires_api_key(self):
        request = self.factory.get(f"/api/sensor-external-api/logs/?farm_uuid={self.farm_uuid}")

        response = SensorExternalRequestLogListAPIView.as_view()(request)

        self.assertEqual(response.status_code, 401)

    def test_returns_paginated_logs_for_farm_uuid(self):
        request = self.factory.get(
            f"/api/sensor-external-api/logs/?farm_uuid={self.farm_uuid}&page=1&page_size=1",
            HTTP_X_API_KEY="12345",
        )

        response = SensorExternalRequestLogListAPIView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["id"], self.second_log.id)
        self.assertEqual(
            response.data["data"][0]["physical_device_uuid"],
            str(self.second_log.physical_device_uuid),
        )
        self.assertEqual(
            response.data["data"][0]["sensor_catalog"]["uuid"],
            str(self.second_catalog.uuid),
        )
        self.assertEqual(
            response.data["data"][0]["sensor_catalog"]["name"],
            self.second_catalog.name,
        )
        self.assertEqual(
            response.data["data"][0]["farm_sensor"]["uuid"],
            str(self.second_sensor.uuid),
        )
        self.assertEqual(
            response.data["data"][0]["farm_sensor"]["physical_device_uuid"],
            str(self.second_sensor.physical_device_uuid),
        )
