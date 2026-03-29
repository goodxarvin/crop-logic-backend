from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory

from crop_zoning.views import ZonesInitialView


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
