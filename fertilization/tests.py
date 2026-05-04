from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from unittest.mock import patch

from external_api_adapter.adapter import AdapterResponse
from farm_hub.models import FarmHub, FarmType
from farmer_calendar.models import FarmerCalendarEvent
from .models import FertilizationPlan, FertilizationRecommendationRequest
from .views import (
    FertilizationPlanDetailView,
    FertilizationPlanListView,
    FertilizationPlanStatusView,
    PlanFromTextView,
    RecommendationDetailView,
    RecommendationListView,
    RecommendView,
)


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
        self.assertEqual(FertilizationPlan.objects.count(), 0)
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
        self.assertEqual(FertilizationPlan.objects.count(), 1)
        saved_request = FertilizationRecommendationRequest.objects.get()
        saved_plan = FertilizationPlan.objects.get()
        self.assertEqual(saved_request.crop_id, "گندم")
        self.assertEqual(saved_request.growth_stage, "vegetative")
        self.assertEqual(saved_plan.source, FertilizationPlan.SOURCE_RECOMMENDATION)
        self.assertEqual(saved_plan.recommendation_id, saved_request.id)
        self.assertFalse(saved_plan.is_active)
        self.assertFalse(saved_plan.is_deleted)
        self.assertEqual(saved_plan.plan_payload["primary_recommendation"]["fertilizer_code"], "npk-202020")
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

    @patch("fertilization.views.external_api_request")
    def test_recommend_includes_active_fertilization_plan_in_ai_payload(self, mock_external_api_request):
        FertilizationPlan.objects.create(
            farm=self.farm,
            source=FertilizationPlan.SOURCE_FREE_TEXT,
            title="برنامه فعال",
            crop_id="گندم",
            growth_stage="vegetative",
            plan_payload={
                "primary_recommendation": {"fertilizer_code": "npk-101010", "fertilizer_name": "NPK 10-10-10"},
                "nutrient_analysis": {"macro": [{"key": "n", "value": 10}]},
                "application_guide": {"steps": [{"step_number": 1, "title": "مرحله اول"}]},
                "sections": [{"type": "recommendation", "title": "اصلی"}],
            },
            is_active=True,
        )
        mock_external_api_request.return_value = AdapterResponse(status_code=200, data={"data": {}})

        request = self.factory.post(
            "/api/fertilization/recommend/",
            {"farm_uuid": str(self.farm.farm_uuid), "crop_id": "گندم", "growth_stage": "vegetative"},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = RecommendView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        sent_payload = mock_external_api_request.call_args.kwargs["payload"]
        self.assertIn("active_fertilization_plan", sent_payload)
        self.assertEqual(
            sent_payload["active_fertilization_plan"]["primary_recommendation"]["fertilizer_code"],
            "npk-101010",
        )

    @patch("fertilization.views.external_api_request")
    def test_plan_from_text_creates_plan_when_final_plan_exists(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={
                "code": 200,
                "msg": "موفق",
                "data": {
                    "status": "completed",
                    "final_plan": {
                        "title": "برنامه کوددهی گندم",
                        "crop_name": "گندم",
                        "growth_stage": "flowering",
                        "items": [{"name": "NPK 20-20-20"}],
                    },
                },
            },
        )

        request = self.factory.post(
            "/api/fertilization/plan-from-text/",
            {"message": "برنامه کودی", "farm_uuid": str(self.farm.farm_uuid)},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = PlanFromTextView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(FertilizationPlan.objects.count(), 1)
        plan = FertilizationPlan.objects.get()
        self.assertEqual(plan.source, FertilizationPlan.SOURCE_FREE_TEXT)
        self.assertEqual(plan.title, "برنامه کوددهی گندم")
        self.assertEqual(plan.crop_id, "گندم")
        self.assertEqual(plan.growth_stage, "flowering")
        self.assertFalse(plan.is_active)
        self.assertFalse(plan.is_deleted)

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


class FertilizationPlanApiTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            username="fert-plan-user",
            password="secret123",
            email="fert-plan@example.com",
            phone_number="09123334455",
        )
        self.farm_type = FarmType.objects.create(name="باغی")
        self.farm = FarmHub.objects.create(owner=self.user, farm_type=self.farm_type, name="fert-plan-farm")
        self.plan = FertilizationPlan.objects.create(
            farm=self.farm,
            source=FertilizationPlan.SOURCE_FREE_TEXT,
            title="برنامه نمونه",
            crop_id="گوجه",
            growth_stage="flowering",
            plan_payload={"items": [{"title": "مرحله اول"}]},
        )

    def test_plan_list_returns_non_deleted_plans(self):
        FertilizationPlan.objects.create(
            farm=self.farm,
            source=FertilizationPlan.SOURCE_RECOMMENDATION,
            title="حذف شده",
            is_deleted=True,
            is_active=False,
        )

        request = self.factory.get(f"/api/fertilization/plans/?farm_uuid={self.farm.farm_uuid}")
        force_authenticate(request, user=self.user)

        response = FertilizationPlanListView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["plan_uuid"], str(self.plan.uuid))
        self.assertEqual(response.data["data"][0]["source"], FertilizationPlan.SOURCE_FREE_TEXT)

    def test_plan_detail_returns_plan_payload(self):
        request = self.factory.get(f"/api/fertilization/plans/{self.plan.uuid}/")
        force_authenticate(request, user=self.user)

        response = FertilizationPlanDetailView.as_view()(request, plan_uuid=self.plan.uuid)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["plan_uuid"], str(self.plan.uuid))
        self.assertEqual(response.data["data"]["plan_payload"]["items"][0]["title"], "مرحله اول")

    def test_plan_delete_is_soft_delete(self):
        request = self.factory.delete(f"/api/fertilization/plans/{self.plan.uuid}/")
        force_authenticate(request, user=self.user)

        response = FertilizationPlanDetailView.as_view()(request, plan_uuid=self.plan.uuid)

        self.assertEqual(response.status_code, 200)
        self.plan.refresh_from_db()
        self.assertTrue(self.plan.is_deleted)
        self.assertFalse(self.plan.is_active)

    def test_plan_status_patch_updates_is_active(self):
        request = self.factory.patch(
            f"/api/fertilization/plans/{self.plan.uuid}/status/",
            {"is_active": True},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = FertilizationPlanStatusView.as_view()(request, plan_uuid=self.plan.uuid)

        self.assertEqual(response.status_code, 200)
        self.plan.refresh_from_db()
        self.assertTrue(self.plan.is_active)

    def test_activating_one_plan_deactivates_other_active_plan(self):
        other_plan = FertilizationPlan.objects.create(
            farm=self.farm,
            source=FertilizationPlan.SOURCE_FREE_TEXT,
            title="برنامه دوم",
            is_active=True,
        )

        request = self.factory.patch(
            f"/api/fertilization/plans/{self.plan.uuid}/status/",
            {"is_active": True},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = FertilizationPlanStatusView.as_view()(request, plan_uuid=self.plan.uuid)

        self.assertEqual(response.status_code, 200)
        self.plan.refresh_from_db()
        other_plan.refresh_from_db()
        self.assertTrue(self.plan.is_active)
        self.assertFalse(other_plan.is_active)

    def test_plan_status_patch_syncs_calendar_events(self):
        self.plan.plan_payload = {
            "primary_recommendation": {
                "fertilizer_code": "npk-202020",
                "fertilizer_name": "NPK 20-20-20",
                "application_interval": {"value": 14, "unit": "day", "label": "هر 14 روز"},
            },
            "application_guide": {
                "steps": [
                    {"step_number": 1, "title": "مرحله اول", "description": "در آب حل شود", "date": "2025-02-14"}
                ]
            },
        }
        self.plan.is_active = False
        self.plan.save(update_fields=["plan_payload", "is_active", "updated_at"])

        activate_request = self.factory.patch(
            f"/api/fertilization/plans/{self.plan.uuid}/status/",
            {"is_active": True},
            format="json",
        )
        force_authenticate(activate_request, user=self.user)

        activate_response = FertilizationPlanStatusView.as_view()(activate_request, plan_uuid=self.plan.uuid)

        self.assertEqual(activate_response.status_code, 200)
        events = FarmerCalendarEvent.objects.filter(farm=self.farm, extended_props__plan_uuid=str(self.plan.uuid))
        self.assertEqual(events.count(), 1)
        self.assertEqual(events.first().extended_props["plan_type"], "fertilization")

        deactivate_request = self.factory.patch(
            f"/api/fertilization/plans/{self.plan.uuid}/status/",
            {"is_active": False},
            format="json",
        )
        force_authenticate(deactivate_request, user=self.user)

        deactivate_response = FertilizationPlanStatusView.as_view()(deactivate_request, plan_uuid=self.plan.uuid)

        self.assertEqual(deactivate_response.status_code, 200)
        self.assertFalse(
            FarmerCalendarEvent.objects.filter(farm=self.farm, extended_props__plan_uuid=str(self.plan.uuid)).exists()
        )
