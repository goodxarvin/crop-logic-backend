from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from sensor_catalog.models import SensorCatalog
from sensor_catalog.views import SensorCatalogListView


class SensorCatalogListViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            username="sensor-user",
            password="secret123",
            email="sensor@example.com",
            phone_number="09120000002",
        )
        SensorCatalog.objects.update_or_create(
            code="sensor_7_soil_moisture_sensor_v1_2",
            name="Sensor 7 - Soil Moisture Sensor v1.2",
            defaults={
                "description": (
                    "Measures only soil moisture using electrical resistance between two metal probes. "
                    "Provides analog and digital outputs."
                ),
                "customizable_fields": [],
                "supported_power_sources": ["solar", "direct_power"],
                "returned_data_fields": ["soil_moisture", "analog_output", "digital_output"],
                "sample_payload": {"soil_moisture": 42, "analog_output": 610, "digital_output": 1},
                "is_active": True,
            },
        )
        SensorCatalog.objects.update_or_create(
            code="legacy_sensor",
            name="Legacy Sensor",
            defaults={
                "customizable_fields": [],
                "supported_power_sources": ["direct_power"],
                "returned_data_fields": ["status"],
                "sample_payload": {"status": "offline"},
                "is_active": False,
            },
        )

    def test_list_returns_all_existing_sensors(self):
        request = self.factory.get("/api/sensor-catalog/")
        force_authenticate(request, user=self.user)

        response = SensorCatalogListView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(len(response.data["data"]), 2)
        self.assertEqual(
            {item["code"] for item in response.data["data"]},
            {"sensor_7_soil_moisture_sensor_v1_2", "legacy_sensor"},
        )
