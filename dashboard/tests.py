from copy import deepcopy

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory

from .mock_data import DEFAULT_CONFIG, reset_config
from .views import FarmDashboardConfigView


class FarmDashboardConfigViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        reset_config()

    def tearDown(self):
        reset_config()

    def test_get_returns_canonical_config(self):
        request = self.factory.get("/api/farm-dashboard-config/")
        response = FarmDashboardConfigView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(response.data["msg"], "OK")
        self.assertEqual(response.data["data"], DEFAULT_CONFIG)

    def test_patch_partial_update_returns_full_final_config(self):
        request = self.factory.patch(
            "/api/farm-dashboard-config/",
            {"disabled_card_ids": ["farmWeatherCard"]},
            format="json",
        )
        response = FarmDashboardConfigView.as_view()(request)

        expected = deepcopy(DEFAULT_CONFIG)
        expected["disabled_card_ids"] = ["farmWeatherCard"]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"], expected)

    def test_patch_only_drag_flag_still_returns_full_config(self):
        request = self.factory.patch(
            "/api/farm-dashboard-config/",
            {"enable_drag_reorder": False},
            format="json",
        )
        response = FarmDashboardConfigView.as_view()(request)

        expected = deepcopy(DEFAULT_CONFIG)
        expected["enable_drag_reorder"] = False

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"], expected)
        self.assertIn("disabled_card_ids", response.data["data"])
        self.assertIn("row_order", response.data["data"])

    def test_patch_rejects_invalid_row_order(self):
        request = self.factory.patch(
            "/api/farm-dashboard-config/",
            {"row_order": ["overviewKpis"]},
            format="json",
        )
        response = FarmDashboardConfigView.as_view()(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("row_order", response.data)
