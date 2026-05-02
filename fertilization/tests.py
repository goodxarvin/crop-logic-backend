from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from unittest.mock import patch

from external_api_adapter.adapter import AdapterResponse
from farm_hub.models import FarmHub, FarmType
from .models import FertilizationRecommendationRequest
from .views import PlanFromTextView, RecommendationDetailView, RecommendationListView, RecommendView


class FertilizationRecommendViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            username="fert-user",
            password="secret123",
            email="fert@example.com",
            phone_number="09125556677",
        )
        self.farm_type = FarmType.objects.create(name="زراعی")
        self.farm = FarmHub.objects.create(owner=self.user, farm_type=self.farm_type, name="fert-farm")

    @patch("fertilization.views.external_api_request")
    def test_plan_from_text_proxies_to_ai_service(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={
                "code": 200,
                "msg": "موفق",
                "data": {
                    "status": "needs_clarification",
                    "status_fa": "نیازمند پرسش تکمیلی",
                    "summary": "need more",
                    "missing_fields": ["growth_stage"],
                    "questions": [{"id": "growth_stage", "field": "growth_stage", "question": "?", "rationale": "!"}],
                    "collected_data": {"crop_name": "گندم"},
                    "final_plan": None,
                },
            },
        )

        request = self.factory.post(
            "/api/fertilization/plan-from-text/",
            {"message": "متن کودهی", "farm_uuid": str(self.farm.farm_uuid)},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = PlanFromTextView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["status"], "needs_clarification")
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/fertilization/plan-from-text/",
            method="POST",
            payload={"message": "متن کودهی", "farm_uuid": str(self.farm.farm_uuid)},
        )

    def test_plan_from_text_requires_message_or_answers_or_partial_plan(self):
        request = self.factory.post("/api/fertilization/plan-from-text/", {}, format="json")
        force_authenticate(request, user=self.user)

        response = PlanFromTextView.as_view()(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("non_field_errors", response.data)

    @patch("fertilization.views.external_api_request")
    def test_recommend_returns_updated_response_shape(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={
                "code": 200,
                "msg": "success",
                "data": {
                    "primary_recommendation": {
                        "fertilizer_code": "npk-202020",
                        "fertilizer_name": "NPK 20-20-20",
                        "display_title": "کود کامل متعادل",
                        "fertilizer_type": "NPK",
                        "npk_ratio": {"n": 20, "p": 20, "k": 20, "label": "20-20-20"},
                        "application_method": {"id": "fertigation", "label": "کودآبیاری"},
                        "application_interval": {"value": 14, "unit": "day", "label": "هر 14 روز"},
                        "dosage": {
                            "base_amount_per_hectare": 65,
                            "base_amount_per_square_meter": 0.0065,
                            "unit": "kg",
                            "label": "65 کیلوگرم در هکتار",
                            "calculation_basis": "engine-v2",
                        },
                        "reasoning": "متعادل برای فاز رشد",
                        "summary": "مصرف منظم در این مرحله توصیه می شود",
                    },
                    "nutrient_analysis": {
                        "macro": [
                            {"key": "n", "name": "Nitrogen", "value": 20, "unit": "percent", "description": "تقویت رشد رویشی"}
                        ],
                        "micro": [
                            {"key": "zn", "name": "Zinc", "value": 2.5, "unit": "percent", "description": "بهبود رشد"}
                        ],
                    },
                    "application_guide": {
                        "safety_warning": "در ساعات خنک مصرف شود",
                        "steps": [
                            {"step_number": 1, "title": "حل کردن", "description": "کود را در آب حل کنید"}
                        ],
                    },
                    "alternative_recommendations": [
                        {
                            "fertilizer_code": "npk-121236",
                            "fertilizer_name": "NPK 12-12-36",
                            "fertilizer_type": "NPK",
                            "usage_method": "fertigation",
                            "description": "برای نیاز پتاس بالا",
                        }
                    ],
                    "sections": [
                        {"type": "recommendation", "title": "پیشنهاد اصلی", "icon": "leaf", "content": "NPK 20-20-20"}
                    ],
                },
            },
        )

        request = self.factory.post(
            "/api/fertilization/recommend/",
            {"farm_uuid": str(self.farm.farm_uuid), "crop_id": "گندم", "growth_stage": "vegetative"},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = RecommendView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertIn("primary_recommendation", response.data["data"])
        self.assertIn("nutrient_analysis", response.data["data"])
        self.assertIn("application_guide", response.data["data"])
        self.assertIn("alternative_recommendations", response.data["data"])
        self.assertEqual(response.data["data"]["primary_recommendation"]["fertilizer_code"], "npk-202020")
        self.assertEqual(response.data["data"]["primary_recommendation"]["application_interval"]["value"], 14.0)
        self.assertEqual(response.data["data"]["alternative_recommendations"][0]["usage_method"], "fertigation")
        self.assertEqual(response.data["data"]["sections"][0]["type"], "recommendation")
        self.assertEqual(FertilizationRecommendationRequest.objects.count(), 1)
        saved_request = FertilizationRecommendationRequest.objects.get()
        self.assertEqual(saved_request.crop_id, "گندم")
        self.assertEqual(saved_request.growth_stage, "vegetative")
        self.assertEqual(
            saved_request.status,
            FertilizationRecommendationRequest.STATUS_PENDING_CONFIRMATION,
        )
        self.assertEqual(
            saved_request.response_payload["data"]["primary_recommendation"]["fertilizer_code"],
            "npk-202020",
        )
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/fertilization/recommend/",
            method="POST",
            payload={
                "farm_uuid": str(self.farm.farm_uuid),
                "crop_id": "گندم",
                "plant_name": "گندم",
                "growth_stage": "vegetative",
            },
        )

    @patch("fertilization.views.external_api_request")
    def test_recommend_accepts_plant_name_and_passes_it_directly_to_ai(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(status_code=200, data={"data": {}})

        request = self.factory.post(
            "/api/fertilization/recommend/",
            {"farm_uuid": str(self.farm.farm_uuid), "plant_name": "جو", "growth_stage": "flowering"},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = RecommendView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        saved_request = FertilizationRecommendationRequest.objects.latest("created_at")
        self.assertEqual(saved_request.crop_id, "جو")
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/fertilization/recommend/",
            method="POST",
            payload={
                "farm_uuid": str(self.farm.farm_uuid),
                "crop_id": "جو",
                "plant_name": "جو",
                "growth_stage": "flowering",
            },
        )

    def test_recommendation_list_returns_paginated_summary_items(self):
        first = FertilizationRecommendationRequest.objects.create(
            farm=self.farm,
            crop_id="گندم",
            growth_stage="vegetative",
            status=FertilizationRecommendationRequest.STATUS_PENDING_CONFIRMATION,
            response_payload={
                "data": {
                    "primary_recommendation": {
                        "fertilizer_type": "NPK",
                    }
                }
            },
        )
        second = FertilizationRecommendationRequest.objects.create(
            farm=self.farm,
            crop_id="ذرت",
            growth_stage="flowering",
            status=FertilizationRecommendationRequest.STATUS_PENDING_CONFIRMATION,
            response_payload={
                "data": {
                    "primary_recommendation": {
                        "fertilizer_type": "Micronutrient",
                    }
                }
            },
        )

        request = self.factory.get(
            f"/api/fertilization/recommendations/?farm_uuid={self.farm.farm_uuid}&page=1&page_size=1"
        )
        force_authenticate(request, user=self.user)

        response = RecommendationListView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["pagination"]["page"], 1)
        self.assertEqual(response.data["pagination"]["page_size"], 1)
        self.assertEqual(response.data["pagination"]["total_pages"], 2)
        self.assertEqual(response.data["pagination"]["total_items"], 2)
        self.assertTrue(response.data["pagination"]["has_next"])
        self.assertFalse(response.data["pagination"]["has_previous"])
        self.assertEqual(response.data["data"][0]["recommendation_uuid"], str(second.uuid))
        self.assertEqual(response.data["data"][0]["plant_name"], "ذرت")
        self.assertEqual(response.data["data"][0]["growth_stage"], "flowering")
        self.assertEqual(response.data["data"][0]["fertilizer_type"], "Micronutrient")
        self.assertEqual(response.data["data"][0]["status"], "pending_confirmation")
        self.assertEqual(response.data["data"][0]["status_label"], "منتظر تایید")
        self.assertIn("requested_at", response.data["data"][0])
        self.assertNotEqual(response.data["data"][0]["recommendation_uuid"], str(first.uuid))

    def test_recommendation_detail_returns_same_shape_as_recommend_endpoint(self):
        recommendation = FertilizationRecommendationRequest.objects.create(
            farm=self.farm,
            crop_id="گندم",
            growth_stage="vegetative",
            status=FertilizationRecommendationRequest.STATUS_PENDING_CONFIRMATION,
            response_payload={
                "data": {
                    "primary_recommendation": {
                        "fertilizer_code": "npk-202020",
                        "fertilizer_type": "NPK",
                        "summary": "خلاصه توصیه",
                    },
                    "nutrient_analysis": {
                        "macro": [{"key": "n", "name": "Nitrogen", "value": 20, "unit": "percent"}],
                        "micro": [],
                    },
                    "application_guide": {
                        "safety_warning": "در هوای خنک استفاده شود",
                        "steps": [{"step_number": 1, "title": "آماده سازی", "description": "در آب حل شود"}],
                    },
                    "alternative_recommendations": [
                        {"fertilizer_code": "alt-1", "fertilizer_name": "Alt", "fertilizer_type": "NPK"}
                    ],
                    "sections": [{"type": "warning", "title": "هشدار", "content": "اختلاط نشود"}],
                }
            },
        )

        request = self.factory.get(f"/api/fertilization/recommendations/{recommendation.uuid}/")
        force_authenticate(request, user=self.user)

        response = RecommendationDetailView.as_view()(request, recommendation_uuid=recommendation.uuid)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(response.data["data"]["primary_recommendation"]["fertilizer_code"], "npk-202020")
        self.assertEqual(response.data["data"]["primary_recommendation"]["fertilizer_type"], "NPK")
        self.assertEqual(response.data["data"]["nutrient_analysis"]["macro"][0]["value"], 20.0)
        self.assertEqual(response.data["data"]["application_guide"]["steps"][0]["step_number"], 1)
        self.assertEqual(response.data["data"]["sections"][0]["type"], "warning")
        self.assertEqual(response.data["data"]["recommendation_uuid"], str(recommendation.uuid))
        self.assertEqual(response.data["data"]["crop_id"], "گندم")
        self.assertEqual(response.data["data"]["plant_name"], "گندم")
        self.assertEqual(response.data["data"]["status"], "pending_confirmation")
        self.assertEqual(response.data["data"]["status_label"], "منتظر تایید")

    def test_recommendation_detail_falls_back_to_top_level_fertilizer_code(self):
        recommendation = FertilizationRecommendationRequest.objects.create(
            farm=self.farm,
            crop_id="گندم",
            growth_stage="vegetative",
            status=FertilizationRecommendationRequest.STATUS_PENDING_CONFIRMATION,
            response_payload={
                "data": {
                    "fertilizer_code": "legacy-code-101",
                    "fertilizer_type": "NPK",
                }
            },
        )

        request = self.factory.get(f"/api/fertilization/recommendations/{recommendation.uuid}/")
        force_authenticate(request, user=self.user)

        response = RecommendationDetailView.as_view()(request, recommendation_uuid=recommendation.uuid)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["data"]["primary_recommendation"]["fertilizer_code"],
            "legacy-code-101",
        )
