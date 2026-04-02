from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory, force_authenticate

from crop_zoning.models import CropArea
from farm_hub.models import FarmType, Product
from farm_hub.seeds import seed_admin_farm
from farm_hub.views import FarmListCreateView


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
class FarmListCreateViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            username="farmer",
            password="secret123",
            email="farmer@example.com",
            phone_number="09120000000",
        )
        self.farm_type, _ = FarmType.objects.get_or_create(name="زراعی")
        self.wheat, _ = Product.objects.get_or_create(farm_type=self.farm_type, name="گندم")

    def test_create_farm_with_area_geojson_creates_crop_zoning_payload(self):
        request = self.factory.post(
            "/api/farm-hub/",
            {
                "name": "farm-1",
                "farm_type_uuid": str(self.farm_type.uuid),
                "product_uuids": [str(self.wheat.uuid)],
                "customization": {"report_interval_sec": 300},
                "sensors": [
                    {
                        "name": "zone-sensor",
                        "sensor_type": "weather_station",
                        "specifications": {"model": "FH-1"},
                        "power_source": {"type": "battery"},
                        "customization": {"report_interval_sec": 300},
                    }
                ],
                "area_geojson": AREA_GEOJSON,
            },
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = FarmListCreateView.as_view()(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["code"], 201)
        self.assertEqual(response.data["data"]["name"], "farm-1")
        self.assertIn("zoning", response.data["data"])
        self.assertEqual(len(response.data["data"]["sensors"]), 1)
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
class FarmSeedTests(TestCase):
    def test_seed_admin_farm_dispatches_crop_logic_flow_on_create(self):
        farm, created = seed_admin_farm()

        self.assertTrue(created)
        self.assertEqual(farm.farm_uuid.hex, "11111111111111111111111111111111")
        self.assertEqual(CropArea.objects.count(), 1)
        self.assertEqual(farm.sensors.count(), 2)

    def test_seed_admin_farm_does_not_dispatch_twice_for_existing_seed(self):
        first_farm, first_created = seed_admin_farm()
        second_farm, second_created = seed_admin_farm()

        self.assertTrue(first_created)
        self.assertFalse(second_created)
        self.assertEqual(first_farm.id, second_farm.id)
        self.assertEqual(CropArea.objects.count(), 1)
