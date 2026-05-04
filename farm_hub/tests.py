from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory, force_authenticate
from unittest.mock import patch

from access_control.models import AccessFeature, AccessRule, FarmAccessProfile, SubscriptionPlan
from access_control.services import build_farm_access_profile
from access_control.views import FarmAccessProfileView
from crop_zoning.models import CropArea
from device_hub.models import SensorCatalog
from external_api_adapter.adapter import AdapterResponse
from farm_hub.models import FarmHub, FarmType, Product
from farm_hub.serializers import FarmHubSerializer
from farm_hub.seeds import seed_admin_farm
from farm_hub.views import FarmDetailView, FarmListCreateView, FarmTypeListView, FarmTypeProductsView


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
    FARM_DATA_API_KEY="farm-data-key",
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
        self.plan = SubscriptionPlan.objects.create(code="gold", name="Gold")
        self.weather_station, _ = SensorCatalog.objects.get_or_create(
            code="sensor_7_soil_moisture_sensor_v1_2",
            name="Sensor 7 - Soil Moisture Sensor v1.2",
            defaults={"supported_power_sources": ["solar", "direct_power"]},
        )

    @patch("farm_hub.services.external_api_request")
    def test_create_farm_with_area_geojson_creates_crop_zoning_payload(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(status_code=201, data={})
        physical_device_uuid = "33333333-3333-3333-3333-333333333333"
        request = self.factory.post(
            "/api/farm-hub/",
            {
                "name": "farm-1",
                "farm_type_uuid": str(self.farm_type.uuid),
                "subscription_plan_uuid": str(self.plan.uuid),
                "product_uuids": [str(self.wheat.uuid)],
                "irrigation_method_id": 3,
                "irrigation_method_name": "Drip",
                "sensors": [
                    {
                        "sensor_catalog_uuid": str(self.weather_station.uuid),
                        "physical_device_uuid": physical_device_uuid,
                        "name": "zone-sensor",
                        "sensor_type": "weather_station",
                        "specifications": {"model": "FH-1"},
                        "power_source": {"type": "battery"},
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
        self.assertEqual(response.data["data"]["subscription_plan"]["code"], self.plan.code)
        self.assertEqual(response.data["data"]["irrigation_method_id"], 3)
        self.assertEqual(response.data["data"]["irrigation_method_name"], "Drip")
        self.assertIn("zoning", response.data["data"])
        self.assertIsNotNone(response.data["data"]["area_uuid"])
        self.assertEqual(len(response.data["data"]["sensors"]), 1)
        self.assertEqual(response.data["data"]["sensors"][0]["sensor_catalog_uuid"], str(self.weather_station.uuid))
        self.assertEqual(response.data["data"]["sensors"][0]["physical_device_uuid"], physical_device_uuid)
        self.assertGreater(response.data["data"]["zoning"]["zone_count"], 1)
        self.assertEqual(
            response.data["data"]["zoning"]["zone_count"],
            CropArea.objects.get().zone_count,
        )
        self.assertEqual(CropArea.objects.count(), 1)
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/farm-data/",
            method="POST",
            payload={
                "farm_uuid": response.data["data"]["farm_uuid"],
                "farm_boundary": AREA_GEOJSON["geometry"],
                "plant_ids": [self.wheat.id],
                "irrigation_method_id": 3,
            },
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-API-Key": "farm-data-key",
                "Authorization": "Api-Key farm-data-key",
            },
        )

    @patch("farm_hub.services.external_api_request")
    def test_create_farm_ignores_client_farm_uuid_and_generates_new_one(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(status_code=201, data={})
        request = self.factory.post(
            "/api/farm-hub/",
            {
                "farm_uuid": "11111111-1111-1111-1111-111111111111",
                "name": "farm-2",
                "farm_type_uuid": str(self.farm_type.uuid),
                "product_uuids": [str(self.wheat.uuid)],
            },
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = FarmListCreateView.as_view()(request)

        self.assertEqual(response.status_code, 201)
        self.assertNotEqual(response.data["data"]["farm_uuid"], "11111111-1111-1111-1111-111111111111")
        self.assertIsNotNone(response.data["data"]["area_uuid"])

    @patch("farm_hub.services.external_api_request")
    def test_create_farm_rejects_unknown_sensor_catalog_uuid(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(status_code=201, data={})
        request = self.factory.post(
            "/api/farm-hub/",
            {
                "name": "farm-3",
                "farm_type_uuid": str(self.farm_type.uuid),
                "product_uuids": [str(self.wheat.uuid)],
                "sensors": [
                    {
                        "sensor_catalog_uuid": "44444444-4444-4444-4444-444444444444",
                        "name": "zone-sensor",
                    }
                ],
            },
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = FarmListCreateView.as_view()(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("sensor_catalog_uuid", response.data["sensors"][0])

    @patch("farm_hub.services.external_api_request")
    def test_create_farm_defaults_to_gold_plan_when_not_provided(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(status_code=201, data={})
        request = self.factory.post(
            "/api/farm-hub/",
            {
                "name": "farm-default-plan",
                "farm_type_uuid": str(self.farm_type.uuid),
                "product_uuids": [str(self.wheat.uuid)],
            },
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = FarmListCreateView.as_view()(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["subscription_plan"]["code"], "gold")

    def test_create_farm_rejects_non_object_sensor_payload(self):
        request = self.factory.post(
            "/api/farm-hub/",
            {
                "name": "farm-invalid-sensor-payload",
                "farm_type_uuid": str(self.farm_type.uuid),
                "product_uuids": [str(self.wheat.uuid)],
                "sensor_payload": ["invalid"],
            },
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = FarmListCreateView.as_view()(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["sensor_payload"], ["`sensor_payload` must be an object."])

    @patch("farm_hub.services.external_api_request")
    def test_patch_farm_forwards_farm_data_fields(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(status_code=201, data={})
        farm = FarmHub.objects.create(
            owner=self.user,
            farm_type=self.farm_type,
            subscription_plan=self.plan,
            name="patch-target",
        )
        farm.products.add(self.wheat)

        request = self.factory.patch(
            f"/api/farm-hub/{farm.farm_uuid}/",
            {
                "farm_boundary": {
                    "corners": [
                        {"lat": 35.70, "lon": 51.39},
                        {"lat": 35.70, "lon": 51.41},
                        {"lat": 35.72, "lon": 51.41},
                        {"lat": 35.72, "lon": 51.39},
                    ]
                },
                "sensor_payload": {"soil_moisture": 45.2},
                "irrigation_method_id": 3,
                "irrigation_method_name": "Drip",
            },
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = FarmDetailView.as_view()(request, farm_uuid=farm.farm_uuid)

        self.assertEqual(response.status_code, 200)
        farm.refresh_from_db()
        self.assertIsNotNone(farm.current_crop_area)
        self.assertEqual(farm.irrigation_method_id, 3)
        self.assertEqual(farm.irrigation_method_name, "Drip")
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/farm-data/",
            method="POST",
            payload={
                "farm_uuid": str(farm.farm_uuid),
                "farm_boundary": {
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
                "sensor_key": "sensor-7-1",
                "sensor_payload": {
                    "sensor-7-1": {"soil_moisture": 45.2},
                },
                "plant_ids": [self.wheat.id],
                "irrigation_method_id": 3,
            },
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-API-Key": "farm-data-key",
                "Authorization": "Api-Key farm-data-key",
            },
        )


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
        self.assertEqual(farm.sensors.count(), 1)
        self.assertEqual(farm.irrigation_method_id, 1)
        self.assertEqual(farm.irrigation_method_name, "آبیاری قطره ای")
        self.assertIsNotNone(farm.sensors.first().physical_device_uuid)
        self.assertTrue(SensorCatalog.objects.filter(code="sensor_7_soil_moisture_sensor_v1_2").exists())

    def test_seed_admin_farm_does_not_dispatch_twice_for_existing_seed(self):
        first_farm, first_created = seed_admin_farm()
        second_farm, second_created = seed_admin_farm()

        self.assertTrue(first_created)
        self.assertFalse(second_created)
        self.assertEqual(first_farm.id, second_farm.id)
        self.assertEqual(CropArea.objects.count(), 1)


class FarmCatalogViewsTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            username="catalog-user",
            password="secret123",
            email="catalog@example.com",
            phone_number="09120000001",
        )
        self.field_farm_type = FarmType.objects.create(name="زراعی")
        self.tree_farm_type = FarmType.objects.create(name="درختی")
        self.wheat = Product.objects.create(
            farm_type=self.field_farm_type,
            name="گندم",
            planting_season="پاییز",
            harvest_time="بهار",
            health_profile={"moisture": {"ideal_value": 65}},
        )
        self.corn = Product.objects.create(farm_type=self.field_farm_type, name="ذرت")
        Product.objects.create(farm_type=self.tree_farm_type, name="سیب")

    def test_farm_type_list_returns_all_farm_types(self):
        request = self.factory.get("/api/farm-hub/farm-types/")
        force_authenticate(request, user=self.user)

        response = FarmTypeListView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(len(response.data["data"]), 2)

    def test_farm_type_products_returns_products_for_selected_type(self):
        request = self.factory.get(f"/api/farm-hub/farm-types/{self.field_farm_type.uuid}/products/")
        force_authenticate(request, user=self.user)

        response = FarmTypeProductsView.as_view()(request, farm_type_uuid=self.field_farm_type.uuid)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual({item["name"] for item in response.data["data"]}, {self.wheat.name, self.corn.name})
        wheat_payload = next(item for item in response.data["data"] if item["name"] == self.wheat.name)
        self.assertEqual(wheat_payload["planting_season"], "پاییز")
        self.assertEqual(wheat_payload["health_profile"]["moisture"]["ideal_value"], 65)

    def test_farm_type_products_returns_404_for_unknown_type(self):
        unknown_farm_type_uuid = "11111111-1111-1111-1111-111111111111"
        request = self.factory.get(f"/api/farm-hub/farm-types/{unknown_farm_type_uuid}/products/")
        force_authenticate(request, user=self.user)

        response = FarmTypeProductsView.as_view()(request, farm_type_uuid=unknown_farm_type_uuid)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["msg"], "Farm type not found.")


class FarmAccessProfileTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            username="feature-user",
            password="secret123",
            email="feature@example.com",
            phone_number="09120000002",
        )
        self.plan = SubscriptionPlan.objects.create(code="starter", name="Starter")
        self.farm_type = FarmType.objects.create(name="گلخانه ای")
        self.product = Product.objects.create(farm_type=self.farm_type, name="خیار")
        self.sensor_catalog = SensorCatalog.objects.create(code="climate_sensor", name="Climate Sensor")
        self.farm = FarmHub.objects.create(
            owner=self.user,
            farm_type=self.farm_type,
            subscription_plan=self.plan,
            name="Feature Farm",
        )
        self.farm.products.add(self.product)
        self.farm.sensors.create(name="Climate Node", sensor_catalog=self.sensor_catalog, sensor_type="climate")

        self.greenhouse_dashboard = AccessFeature.objects.create(
            code="greenhouse-dashboard",
            name="Greenhouse Dashboard",
            feature_type=AccessFeature.PAGE,
        )
        self.sensor_analytics = AccessFeature.objects.create(
            code="sensor-analytics",
            name="Sensor Analytics",
            feature_type=AccessFeature.WIDGET,
        )
        self.legacy_reports = AccessFeature.objects.create(
            code="legacy-reports",
            name="Legacy Reports",
            feature_type=AccessFeature.PAGE,
            default_enabled=True,
        )

        plan_rule = AccessRule.objects.create(code="starter-greenhouse", name="Starter Greenhouse", priority=10)
        plan_rule.features.add(self.greenhouse_dashboard)
        plan_rule.subscription_plans.add(self.plan)
        plan_rule.farm_types.add(self.farm_type)

        sensor_rule = AccessRule.objects.create(code="sensor-analytics-rule", name="Sensor Analytics", priority=20)
        sensor_rule.features.add(self.sensor_analytics)
        sensor_rule.sensor_catalogs.add(self.sensor_catalog)

        deny_rule = AccessRule.objects.create(
            code="hide-legacy-reports",
            name="Hide Legacy Reports",
            priority=30,
            effect=AccessRule.DENY,
        )
        deny_rule.features.add(self.legacy_reports)
        deny_rule.products.add(self.product)

    def test_build_farm_access_profile_resolves_combined_rules(self):
        profile = build_farm_access_profile(self.farm)

        self.assertEqual(profile["subscription_plan"]["code"], self.plan.code)
        self.assertTrue(profile["features"]["greenhouse-dashboard"]["enabled"])
        self.assertTrue(profile["features"]["sensor-analytics"]["enabled"])
        self.assertFalse(profile["features"]["legacy-reports"]["enabled"])
        self.assertEqual(profile["features"]["legacy-reports"]["source"], "hide-legacy-reports")
        self.assertEqual(len(profile["matched_rules"]), 3)

    def test_access_profile_view_returns_grouped_features(self):
        request = self.factory.get(f"/api/access-control/farms/{self.farm.farm_uuid}/profile/")
        force_authenticate(request, user=self.user)

        response = FarmAccessProfileView.as_view()(request, farm_uuid=self.farm.farm_uuid)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("features", response.data["data"])
        self.assertNotIn("groups", response.data["data"])
        self.assertEqual(len(response.data["data"]["matched_rules"]), 3)
        self.assertTrue(FarmAccessProfile.objects.filter(farm=self.farm).exists())

    def test_sensor_rule_can_match_by_metadata_sensor_code(self):
        sensor_page = AccessFeature.objects.create(
            code="sensor-page",
            name="Sensor Page",
            feature_type=AccessFeature.PAGE,
        )
        sensor_rule = AccessRule.objects.create(
            code="sensor-page-by-code",
            name="Sensor Page By Code",
            priority=40,
            metadata={"sensor_catalog_codes": [self.sensor_catalog.code]},
        )
        sensor_rule.features.add(sensor_page)

        profile = build_farm_access_profile(self.farm)

        self.assertTrue(profile["features"]["sensor-page"]["enabled"])

    def test_build_farm_access_profile_falls_back_to_default_plan(self):
        default_plan = SubscriptionPlan.objects.create(code="gold", name="Gold", metadata={"is_default": True})
        fallback_farm = FarmHub.objects.create(
            owner=self.user,
            farm_type=self.farm_type,
            subscription_plan=None,
            name="Fallback Plan Farm",
        )
        fallback_farm.products.add(self.product)
        fallback_feature = AccessFeature.objects.create(
            code="fallback-dashboard",
            name="Fallback Dashboard",
            feature_type=AccessFeature.PAGE,
        )
        fallback_rule = AccessRule.objects.create(code="gold-fallback-rule", name="Gold Fallback Rule", priority=5)
        fallback_rule.features.add(fallback_feature)
        fallback_rule.subscription_plans.add(default_plan)

        profile = build_farm_access_profile(fallback_farm)

        self.assertEqual(profile["subscription_plan"]["code"], "gold")
        self.assertTrue(profile["features"]["fallback-dashboard"]["enabled"])

    def test_farm_serializer_returns_default_plan_when_model_plan_is_null(self):
        SubscriptionPlan.objects.create(code="gold", name="Gold", metadata={"is_default": True})
        fallback_farm = FarmHub.objects.create(
            owner=self.user,
            farm_type=self.farm_type,
            subscription_plan=None,
            name="Serializer Fallback Farm",
        )

        payload = FarmHubSerializer(fallback_farm).data

        self.assertEqual(payload["subscription_plan"]["code"], "gold")
