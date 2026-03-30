from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory, force_authenticate

from crop_zoning.models import CropArea
from sensor_hub.seeds import seed_admin_sensor
from sensor_hub.views import SensorListCreateView


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
class SensorListCreateViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            username="farmer",
            password="secret123",
            email="farmer@example.com",
            phone_number="09120000000",
        )

    def test_create_sensor_with_area_geojson_creates_crop_zoning_payload(self):
        request = self.factory.post(
            "/api/sensor-hub/",
            {
                "name": "zone-sensor",
                "specifications": {"model": "SH-1"},
                "power_source": {"type": "battery"},
                "customized_sensors": {"report_interval_sec": 300},
                "area_geojson": AREA_GEOJSON,
            },
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = SensorListCreateView.as_view()(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["code"], 201)
        self.assertEqual(response.data["data"]["name"], "zone-sensor")
        self.assertIn("zoning", response.data["data"])
        self.assertGreater(response.data["data"]["zoning"]["zone_count"], 1)
        self.assertEqual(
            response.data["data"]["zoning"]["zone_count"],
            CropArea.objects.get().zone_count,
        )
        self.assertEqual(CropArea.objects.count(), 1)


@override_settings(
    USE_EXTERNAL_API_MOCK=True,
    CROP_ZONE_CHUNK_AREA_SQM=200000,
)
class SensorSeedTests(TestCase):
    def test_seed_admin_sensor_dispatches_crop_logic_flow_on_create(self):
        sensor, created = seed_admin_sensor()

        self.assertTrue(created)
        self.assertEqual(sensor.uuid_sensor.hex, "11111111111111111111111111111111")
        self.assertEqual(CropArea.objects.count(), 1)

    def test_seed_admin_sensor_does_not_dispatch_twice_for_existing_seed(self):
        first_sensor, first_created = seed_admin_sensor()
        second_sensor, second_created = seed_admin_sensor()

        self.assertTrue(first_created)
        self.assertFalse(second_created)
        self.assertEqual(first_sensor.id, second_sensor.id)
        self.assertEqual(CropArea.objects.count(), 1)
