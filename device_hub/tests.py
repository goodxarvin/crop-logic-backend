from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from farm_hub.models import FarmHub, FarmType

from .models import DeviceCatalog, SensorExternalRequestLog
from .services import DeviceDataUnavailableError, build_device_anomaly_detection_card
from .views import DeviceCommandView, DeviceDetailView, DeviceLatestPayloadView, DeviceSummaryView


class DeviceHubGenericViewsTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            username="device-user",
            password="secret123",
            email="device@example.com",
            phone_number="09120001000",
        )
        self.farm_type = FarmType.objects.create(name="گلخانه ای")
        self.farm = FarmHub.objects.create(
            owner=self.user,
            farm_type=self.farm_type,
            name="Device Farm",
        )
        self.catalog = DeviceCatalog.objects.create(
            code="soil_sensor_v2",
            name="Soil Sensor V2",
            device_communication_type=DeviceCatalog.OUTPUT_ONLY,
            returned_data_fields=["soil_moisture", "soil_temperature"],
            payload_mapping={
                "soil_moisture": ["moisture", "soil_moisture"],
                "soil_temperature": ["temperature", "soil_temperature"],
            },
            display_schema={
                "fields": [
                    {"id": "soil_moisture", "label": "رطوبت خاک", "unit": "%", "ideal_min": 40, "ideal_max": 70},
                    {"id": "soil_temperature", "label": "دمای خاک", "unit": "°C", "ideal_min": 18, "ideal_max": 30},
                ]
            },
            supported_widgets=["values_list", "comparison_chart", "radar_chart"],
        )
        self.device = self.farm.sensors.create(
            name="Soil Device 1",
            sensor_catalog=self.catalog,
            sensor_type="soil",
        )
        SensorExternalRequestLog.objects.create(
            farm_uuid=self.farm.farm_uuid,
            sensor_catalog_uuid=self.catalog.uuid,
            physical_device_uuid=self.device.physical_device_uuid,
            payload={"moisture": 52.4, "temperature": 23.1},
        )

    def test_device_detail_view_returns_generic_payload(self):
        request = self.factory.get(
            f"/api/device-hub/devices/{self.device.physical_device_uuid}/",
            {"device_code": self.catalog.code},
        )
        force_authenticate(request, user=self.user)

        response = DeviceDetailView.as_view()(request, physical_device_uuid=self.device.physical_device_uuid)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["physical_device_uuid"], str(self.device.physical_device_uuid))
        self.assertEqual(response.data["data"]["device_catalog"]["code"], self.catalog.code)

    def test_device_latest_payload_view_returns_normalized_readings(self):
        request = self.factory.get(
            f"/api/device-hub/devices/{self.device.physical_device_uuid}/latest/",
            {"device_code": self.catalog.code},
        )
        force_authenticate(request, user=self.user)

        response = DeviceLatestPayloadView.as_view()(request, physical_device_uuid=self.device.physical_device_uuid)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["normalized_payload"]["soil_moisture"], 52.4)
        self.assertEqual(response.data["data"]["readings"]["soil_temperature"], 23.1)

    def test_device_summary_view_returns_supported_widgets(self):
        request = self.factory.get(
            f"/api/device-hub/devices/{self.device.physical_device_uuid}/summary/",
            {"device_code": self.catalog.code},
        )
        force_authenticate(request, user=self.user)

        response = DeviceSummaryView.as_view()(request, physical_device_uuid=self.device.physical_device_uuid)

        self.assertEqual(response.status_code, 200)
        self.assertIn("values_list", response.data["data"]["supportedWidgets"])
        self.assertIn("sensorValuesList", response.data["data"])

    def test_device_summary_view_returns_validation_error_when_history_missing(self):
        SensorExternalRequestLog.objects.all().delete()
        request = self.factory.get(
            f"/api/device-hub/devices/{self.device.physical_device_uuid}/summary/",
            {"device_code": self.catalog.code},
        )
        force_authenticate(request, user=self.user)

        response = DeviceSummaryView.as_view()(request, physical_device_uuid=self.device.physical_device_uuid)

        self.assertEqual(response.status_code, 400)
        self.assertIn("no device history found", response.data["device_code"][0].lower())

    def test_build_device_anomaly_detection_card_returns_explicit_empty_success(self):
        payload = build_device_anomaly_detection_card(self.device)

        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["source"], "db")
        self.assertEqual(payload["anomalies"], [])
        self.assertTrue(payload["warnings"])

    def test_input_only_device_command_view_rejects_input_only_device_code(self):
        input_catalog = DeviceCatalog.objects.create(
            code="valve_v1",
            name="Valve V1",
            device_communication_type=DeviceCatalog.INPUT_ONLY,
            commands_schema=[
                {"command": "open", "label": "Open", "payload_schema": {"duration_seconds": "integer"}},
            ],
        )
        input_device = self.farm.sensors.create(
            name="Valve 1",
            sensor_catalog=input_catalog,
            sensor_type="valve",
        )
        request = self.factory.post(
            f"/api/device-hub/devices/{input_device.physical_device_uuid}/commands/",
            {"device_code": input_catalog.code, "command": "open", "payload": {"duration_seconds": 120}},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = DeviceCommandView.as_view()(request, physical_device_uuid=input_device.physical_device_uuid)

        self.assertEqual(response.status_code, 400)
        self.assertIn("device_code", response.data)
