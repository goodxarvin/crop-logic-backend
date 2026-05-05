from copy import deepcopy

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from access_control.models import AccessFeature, AccessRule
from farm_hub.models import FarmHub, FarmType

from .defaults import DEFAULT_CONFIG
from .models import FarmDashboardConfig
from .views import FarmDashboardCardsView, FarmDashboardConfigView


class DashboardBaseTestCase(TestCase):
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
        self.farm = FarmHub.objects.create(owner=self.user, farm_type=self.farm_type, name="Farm 1")
        self.other_farm = FarmHub.objects.create(owner=self.other_user, farm_type=self.farm_type, name="Farm 2")
        self.dashboard_feature = AccessFeature.objects.create(
            code="greenhouse-dashboard",
            name="Greenhouse Dashboard",
            feature_type=AccessFeature.PAGE,
        )
        self.allow_dashboard_rule = AccessRule.objects.create(
            code="allow-greenhouse-dashboard",
            name="Allow Greenhouse Dashboard",
            priority=10,
        )
        self.allow_dashboard_rule.features.add(self.dashboard_feature)


class FarmDashboardConfigViewTests(DashboardBaseTestCase):
    def test_get_returns_default_config_and_persists_it(self):
        request = self.factory.get(f"/api/farm-dashboard-config/?farm_uuid={self.farm.farm_uuid}")
        force_authenticate(request, user=self.user)
        response = FarmDashboardConfigView.as_view()(request)

        expected = deepcopy(DEFAULT_CONFIG)
        expected["farm_uuid"] = str(self.farm.farm_uuid)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(response.data["msg"], "OK")
        self.assertEqual(response.data["data"], expected)
        self.assertTrue(FarmDashboardConfig.objects.filter(farm=self.farm).exists())

    def test_get_requires_farm_uuid(self):
        request = self.factory.get("/api/farm-dashboard-config/")
        force_authenticate(request, user=self.user)
        response = FarmDashboardConfigView.as_view()(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["farm_uuid"][0], "This field is required.")

    def test_get_rejects_foreign_farm_uuid(self):
        request = self.factory.get(f"/api/farm-dashboard-config/?farm_uuid={self.other_farm.farm_uuid}")
        force_authenticate(request, user=self.user)
        response = FarmDashboardConfigView.as_view()(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["farm_uuid"][0], "Farm not found.")

    def test_patch_partial_update_returns_full_final_config(self):
        request = self.factory.patch(
            "/api/farm-dashboard-config/",
            {
                "farm_uuid": str(self.farm.farm_uuid),
                "disabled_card_ids": ["farmWeatherCard"],
            },
            format="json",
        )
        force_authenticate(request, user=self.user)
        response = FarmDashboardConfigView.as_view()(request)

        expected = deepcopy(DEFAULT_CONFIG)
        expected["farm_uuid"] = str(self.farm.farm_uuid)
        expected["disabled_card_ids"] = ["farmWeatherCard"]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"], expected)
        self.assertEqual(
            FarmDashboardConfig.objects.get(farm=self.farm).disabled_card_ids,
            ["farmWeatherCard"],
        )

    def test_patch_only_drag_flag_still_returns_full_config(self):
        request = self.factory.patch(
            "/api/farm-dashboard-config/",
            {
                "farm_uuid": str(self.farm.farm_uuid),
                "enable_drag_reorder": False,
            },
            format="json",
        )
        force_authenticate(request, user=self.user)
        response = FarmDashboardConfigView.as_view()(request)

        expected = deepcopy(DEFAULT_CONFIG)
        expected["farm_uuid"] = str(self.farm.farm_uuid)
        expected["enable_drag_reorder"] = False

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"], expected)
        self.assertIn("disabled_card_ids", response.data["data"])
        self.assertIn("row_order", response.data["data"])

    def test_patch_rejects_invalid_row_order(self):
        request = self.factory.patch(
            "/api/farm-dashboard-config/",
            {
                "farm_uuid": str(self.farm.farm_uuid),
                "row_order": ["overviewKpis"],
            },
            format="json",
        )
        force_authenticate(request, user=self.user)
        response = FarmDashboardConfigView.as_view()(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("row_order", response.data)


class FarmDashboardCardsViewTests(DashboardBaseTestCase):
    def test_get_returns_locally_aggregated_cards(self):
        request = self.factory.get(f"/api/farm-dashboard/?farm_uuid={self.farm.farm_uuid}")
        force_authenticate(request, user=self.user)

        response = FarmDashboardCardsView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(response.data["msg"], "OK")
        self.assertIn("farmWeatherCard", response.data["data"])
        self.assertIn("farmAlertsTracker", response.data["data"])
        self.assertIn("yieldPredictionChart", response.data["data"])
        self.assertIn("ndviHealthCard", response.data["data"])
        self.assertIn("sensorRadarChart", response.data["data"])
        self.assertIn("soilMoistureHeatmap", response.data["data"])
        self.assertIn("economicOverview", response.data["data"])
        self.assertEqual(response.data["data"]["farmOverviewKpis"]["kpis"][0]["id"], "farm_health_score")
        self.assertEqual(response.data["data"]["farmOverviewKpis"]["kpis"][2]["id"], "avg_soil_moisture")

    def test_get_requires_farm_uuid(self):
        request = self.factory.get("/api/farm-dashboard/")
        force_authenticate(request, user=self.user)

        response = FarmDashboardCardsView.as_view()(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["farm_uuid"][0], "This field is required.")

    def test_get_denies_access_when_feature_is_blocked(self):
        deny_rule = AccessRule.objects.create(
            code="deny-greenhouse-dashboard",
            name="Deny Greenhouse Dashboard",
            priority=20,
            effect=AccessRule.DENY,
        )
        deny_rule.features.add(self.dashboard_feature)

        request = self.factory.get(f"/api/farm-dashboard/?farm_uuid={self.farm.farm_uuid}")
        force_authenticate(request, user=self.user)

        response = FarmDashboardCardsView.as_view()(request)

        self.assertEqual(response.status_code, 403)
