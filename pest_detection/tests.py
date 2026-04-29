from unittest.mock import patch

from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import resolve
from rest_framework.test import APIRequestFactory, force_authenticate

from external_api_adapter.adapter import AdapterResponse
from farm_hub.models import FarmHub, FarmType, Product

from .views import AnalyzeView, RiskSummaryView, RiskView


TEST_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "pest-detection-tests",
    }
}

TEST_RISK_SUMMARY_CACHE_TTL = 14400


@override_settings(
    CACHES=TEST_CACHES,
    PEST_DISEASE_RISK_SUMMARY_CACHE_TTL=TEST_RISK_SUMMARY_CACHE_TTL,
)
class PestDetectionViewTests(TestCase):
    def setUp(self):
        cache.clear()
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
        self.product = Product.objects.create(farm_type=self.farm_type, name="پیاز")
        self.farm.products.add(self.product)
        self.other_farm = FarmHub.objects.create(owner=self.other_user, farm_type=self.farm_type, name="Farm 2")

    @patch("pest_detection.views.external_api_request")
    def test_analyze_proxies_to_ai_service(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={
                "data": {
                    "result": {
                        "has_issue": True,
                        "category": "disease",
                        "confidence": 0.93,
                        "severity": "medium",
                        "summary": "Leaf spot symptoms detected.",
                        "detected_signs": ["Brown leaf spots"],
                        "possible_causes": ["Fungal pressure"],
                        "immediate_actions": ["Isolate affected plants"],
                        "reasoning": ["Pattern matched common fungal lesions"],
                    }
                }
            },
        )

        request = self.factory.post(
            "/api/pest-detection/analyze/",
            {"farm_uuid": str(self.farm.farm_uuid), "image_urls": ["https://example.com/leaf.jpg"]},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = AnalyzeView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(response.data["data"]["category"], "disease")
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/pest-disease/detect/",
            method="POST",
            payload={
                "farm_uuid": str(self.farm.farm_uuid),
                "plant_name": "",
                "query": "",
                "image_urls": ["https://example.com/leaf.jpg"],
            },
        )

    def test_analyze_requires_at_least_one_image(self):
        request = self.factory.post(
            "/api/pest-detection/analyze/",
            {"farm_uuid": str(self.farm.farm_uuid)},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = AnalyzeView.as_view()(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], 400)
        self.assertIn("images", response.data["data"])

    @patch("pest_detection.views.external_api_request")
    def test_risk_proxies_to_ai_service(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={
                "data": {
                    "result": {
                        "summary": "Warm humidity raises fungal pressure.",
                        "forecast_window": "72h",
                        "overall_risk": "medium",
                        "disease_risk": {"score": 0.7, "level": "medium", "likely_conditions": [], "reasoning": []},
                        "pest_risk": {"score": 0.4, "level": "low", "likely_conditions": [], "reasoning": []},
                        "key_drivers": ["High humidity"],
                        "recommended_actions": ["Scout vulnerable rows"],
                    }
                }
            },
        )

        request = self.factory.post(
            "/api/pest-detection/risk/",
            {"farm_uuid": str(self.farm.farm_uuid), "plant_name": "wheat"},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = RiskView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["overall_risk"], "medium")
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/pest-disease/risk/",
            method="POST",
            payload={
                "farm_uuid": str(self.farm.farm_uuid),
                "plant_name": "wheat",
                "growth_stage": "",
            },
        )

    @patch("pest_detection.views.external_api_request")
    def test_risk_summary_maps_response_shape(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={
                "data": {
                    "result": {
                        "disease_risk": {"title": "Disease"},
                        "pest_risk": {"title": "Pest"},
                        "drivers": {"humidity": "high"},
                    }
                }
            },
        )

        request = self.factory.post(
            "/api/pest-disease/risk-summary/",
            {"farm_uuid": str(self.farm.farm_uuid)},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = RiskSummaryView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(response.data["data"]["farm_uuid"], str(self.farm.farm_uuid))
        self.assertEqual(response.data["data"]["diseaseRisk"]["title"], "Disease")
        self.assertEqual(response.data["data"]["pestRisk"]["title"], "Pest")
        self.assertEqual(response.data["data"]["drivers"], {"humidity": "high"})
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/pest-disease/risk/",
            method="POST",
            payload={
                "farm_uuid": str(self.farm.farm_uuid),
                "plant_name": "پیاز",
                "growth_stage": "گلدهی",
            },
        )

    @patch("pest_detection.views.external_api_request")
    def test_risk_summary_post_uses_pest_disease_route(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={
                "data": {
                    "result": {
                        "disease_risk": {"title": "Disease"},
                        "pest_risk": {"title": "Pest"},
                        "drivers": {"humidity": "high"},
                    }
                }
            },
        )

        request = self.factory.post(
            "/api/pest-disease/risk-summary/",
            {"farm_uuid": str(self.farm.farm_uuid)},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = RiskSummaryView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["farm_uuid"], str(self.farm.farm_uuid))
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/pest-disease/risk/",
            method="POST",
            payload={
                "farm_uuid": str(self.farm.farm_uuid),
                "plant_name": "پیاز",
                "growth_stage": "گلدهی",
            },
        )

    @patch("pest_detection.views.external_api_request")
    def test_risk_summary_uses_blank_plant_name_when_farm_has_no_products(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={
                "data": {
                    "result": {
                        "disease_risk": {"title": "Disease"},
                        "pest_risk": {"title": "Pest"},
                        "drivers": {},
                    }
                }
            },
        )
        farm_without_products = FarmHub.objects.create(owner=self.user, farm_type=self.farm_type, name="Farm 3")

        request = self.factory.post(
            "/api/pest-disease/risk-summary/",
            {"farm_uuid": str(farm_without_products.farm_uuid)},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = RiskSummaryView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/pest-disease/risk/",
            method="POST",
            payload={
                "farm_uuid": str(farm_without_products.farm_uuid),
                "plant_name": "",
                "growth_stage": "گلدهی",
            },
        )

    @patch("pest_detection.views.external_api_request")
    def test_risk_summary_caches_last_four_responses(self, mock_external_api_request):
        for index in range(5):
            product = Product.objects.create(farm_type=self.farm_type, name=f"Product {index}")
            farm = FarmHub.objects.create(owner=self.user, farm_type=self.farm_type, name=f"Farm {index + 10}")
            farm.products.add(product)
            mock_external_api_request.return_value = AdapterResponse(
                status_code=200,
                data={
                    "data": {
                        "result": {
                            "disease_risk": {"title": f"Disease {index}"},
                            "pest_risk": {"title": f"Pest {index}"},
                            "drivers": {"index": index},
                        }
                    }
                },
            )

            request = self.factory.post(
                "/api/pest-disease/risk-summary/",
                {"farm_uuid": str(farm.farm_uuid)},
                format="json",
            )
            force_authenticate(request, user=self.user)
            response = RiskSummaryView.as_view()(request)

            self.assertEqual(response.status_code, 200)

        cached_items = cache.get(RiskSummaryView.RISK_SUMMARY_CACHE_KEY)

        self.assertEqual(len(cached_items), 4)
        self.assertEqual(cached_items[0]["drivers"], {"index": 4})
        self.assertEqual(cached_items[-1]["drivers"], {"index": 1})

    @patch("pest_detection.views.external_api_request")
    def test_risk_summary_returns_cached_response_for_same_farm(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={
                "data": {
                    "result": {
                        "disease_risk": {"title": "Disease"},
                        "pest_risk": {"title": "Pest"},
                        "drivers": {"humidity": "high"},
                    }
                }
            },
        )

        for _ in range(2):
            request = self.factory.post(
                "/api/pest-disease/risk-summary/",
                {"farm_uuid": str(self.farm.farm_uuid)},
                format="json",
            )
            force_authenticate(request, user=self.user)
            response = RiskSummaryView.as_view()(request)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data["data"]["drivers"], {"humidity": "high"})

        cache_key = RiskSummaryView._build_risk_summary_cache_key(self.user.id, self.farm.farm_uuid)
        self.assertEqual(cache.get(cache_key)["farm_uuid"], str(self.farm.farm_uuid))
        mock_external_api_request.assert_called_once()

    @patch("pest_detection.views.cache.set")
    @patch("pest_detection.views.external_api_request")
    def test_risk_summary_uses_env_ttl_for_cache(self, mock_external_api_request, mock_cache_set):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={
                "data": {
                    "result": {
                        "disease_risk": {"title": "Disease"},
                        "pest_risk": {"title": "Pest"},
                        "drivers": {},
                    }
                }
            },
        )

        request = self.factory.post(
            "/api/pest-disease/risk-summary/",
            {"farm_uuid": str(self.farm.farm_uuid)},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = RiskSummaryView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            any(call.kwargs.get("timeout") == TEST_RISK_SUMMARY_CACHE_TTL for call in mock_cache_set.call_args_list)
        )

    def test_risk_summary_rejects_extra_fields(self):
        request = self.factory.post(
            "/api/pest-disease/risk-summary/",
            {
                "farm_uuid": str(self.farm.farm_uuid),
                "plant_name": "گندم",
                "growth_stage": "رشد رویشی",
            },
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = RiskSummaryView.as_view()(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], 400)
        self.assertIn("non_field_errors", response.data["data"])

    def test_risk_summary_rejects_foreign_farm_uuid(self):
        request = self.factory.post(
            "/api/pest-disease/risk-summary/",
            {"farm_uuid": str(self.other_farm.farm_uuid)},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = RiskSummaryView.as_view()(request)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["code"], 404)
        self.assertEqual(response.data["data"]["farm_uuid"][0], "Farm not found.")

    def test_risk_summary_get_is_not_allowed(self):
        request = self.factory.get(f"/api/pest-disease/risk-summary/?farm_uuid={self.farm.farm_uuid}")
        force_authenticate(request, user=self.user)

        response = RiskSummaryView.as_view()(request)

        self.assertEqual(response.status_code, 405)

    def test_pest_disease_alias_routes_exist(self):
        self.assertIs(resolve("/api/pest-disease/detect/").func.view_class, AnalyzeView)
        self.assertIs(resolve("/api/pest-disease/risk/").func.view_class, RiskView)
        self.assertIs(resolve("/api/pest-disease/risk-summary/").func.view_class, RiskSummaryView)
