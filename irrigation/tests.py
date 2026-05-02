from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from external_api_adapter.adapter import AdapterResponse
from farm_hub.models import FarmHub, FarmType

from .models import IrrigationPlan, IrrigationRecommendationRequest
from .views import (
    IrrigationMethodListView,
    IrrigationPlanDetailView,
    IrrigationPlanListView,
    IrrigationPlanStatusView,
    PlanFromTextView,
    RecommendView,
    RecommendationDetailView,
    RecommendationListView,
    WaterStressView,
)


class WaterStressViewTests(TestCase):
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

    @patch("irrigation.views.external_api_request")
    def test_post_proxies_request_to_ai_service(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={
                "data": {
                    "result": {
                        "waterStressIndex": 12,
                        "level": "پایین",
                        "sourceMetric": {"soilMoisture": 24},
                    }
                }
            },
        )

        request = self.factory.post(
            "/api/irrigation/water-stress/",
            {"farm_uuid": str(self.farm.farm_uuid)},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = WaterStressView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(response.data["msg"], "success")
        self.assertEqual(response.data["data"]["farm_uuid"], str(self.farm.farm_uuid))
        self.assertEqual(response.data["data"]["waterStressIndex"], 12)
        self.assertEqual(response.data["data"]["level"], "پایین")
        self.assertEqual(response.data["data"]["sourceMetric"], {"soilMoisture": 24})
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/irrigation/water-stress/",
            method="POST",
            payload={"farm_uuid": str(self.farm.farm_uuid)},
        )

    def test_post_rejects_foreign_farm_uuid(self):
        request = self.factory.post(
            "/api/irrigation/water-stress/",
            {"farm_uuid": str(self.other_farm.farm_uuid)},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = WaterStressView.as_view()(request)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["code"], 404)
        self.assertEqual(response.data["data"]["farm_uuid"][0], "Farm not found.")


class IrrigationPlanFromTextViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            username="plan-parser-user",
            password="secret123",
            email="plan-parser@example.com",
            phone_number="09120000005",
        )
        self.farm_type = FarmType.objects.create(name="گلخانه ای")
        self.farm = FarmHub.objects.create(owner=self.user, farm_type=self.farm_type, name="Plan Parser Farm")

    @patch("irrigation.views.external_api_request")
    def test_plan_from_text_proxies_to_ai_service(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={
                "code": 200,
                "msg": "موفق",
                "data": {
                    "status": "completed",
                    "status_fa": "تکمیل شد",
                    "summary": "done",
                    "missing_fields": [],
                    "questions": [],
                    "collected_data": {"crop_name": "گوجه فرنگی"},
                    "final_plan": {"crop_name": "گوجه فرنگی"},
                },
            },
        )

        request = self.factory.post(
            "/api/irrigation/plan-from-text/",
            {"message": "متن برنامه", "farm_uuid": str(self.farm.farm_uuid)},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = PlanFromTextView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["status"], "completed")
        self.assertEqual(IrrigationPlan.objects.count(), 1)
        plan = IrrigationPlan.objects.get()
        self.assertEqual(plan.source, IrrigationPlan.SOURCE_FREE_TEXT)
        self.assertEqual(plan.crop_id, "گوجه فرنگی")
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/irrigation/plan-from-text/",
            method="POST",
            payload={"message": "متن برنامه", "farm_uuid": str(self.farm.farm_uuid)},
        )

    def test_plan_from_text_requires_message_or_answers_or_partial_plan(self):
        request = self.factory.post("/api/irrigation/plan-from-text/", {}, format="json")
        force_authenticate(request, user=self.user)

        response = PlanFromTextView.as_view()(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("non_field_errors", response.data)


class IrrigationMethodListViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    @patch("irrigation.views.external_api_request")
    def test_get_proxies_irrigation_methods_from_ai(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={
                "data": [
                    {
                        "id": 1,
                        "name": "Drip",
                        "category": "micro",
                        "description": "Efficient irrigation",
                        "water_efficiency_percent": 90.0,
                    }
                ]
            },
        )

        request = self.factory.get("/api/irrigation/")
        response = IrrigationMethodListView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(response.data["data"][0]["name"], "Drip")
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/irrigation/",
            method="GET",
        )

    @patch("irrigation.views.external_api_request")
    def test_post_proxies_irrigation_method_creation_to_ai(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=201,
            data={
                "data": {
                    "id": 1,
                    "name": "Drip",
                    "category": "micro",
                }
            },
        )

        request = self.factory.post("/api/irrigation/", {"name": "Drip"}, format="json")
        response = IrrigationMethodListView.as_view()(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["name"], "Drip")
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/irrigation/",
            method="POST",
            payload={"name": "Drip"},
        )


class RecommendViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            username="recommend-farmer",
            password="secret123",
            email="recommend@example.com",
            phone_number="09120000002",
        )
        self.farm_type = FarmType.objects.create(name="باغی")
        self.farm = FarmHub.objects.create(
            owner=self.user,
            farm_type=self.farm_type,
            name="Recommend Farm",
            irrigation_method_id=3,
            irrigation_method_name="آبیاری قطره ای",
        )

    @patch("irrigation.views.external_api_request")
    def test_post_returns_full_recommendation_shape(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={
                "data": {
                    "result": {
                        "plan": {
                            "frequencyPerWeek": 4,
                            "durationMinutes": 38,
                            "bestTimeOfDay": "05:30 تا 08:00 صبح",
                            "moistureLevel": 72,
                            "warning": "در ساعات گرم روز آبیاری انجام نشود",
                        },
                        "water_balance": {
                            "active_kc": 0.93,
                            "crop_profile": {
                                "kc_initial": 0.55,
                                "kc_mid": 1.05,
                                "kc_end": 0.78,
                            },
                            "daily": [
                                {
                                    "forecast_date": "2025-02-12",
                                    "et0_mm": 5.4,
                                    "etc_mm": 4.9,
                                    "effective_rainfall_mm": 0,
                                    "gross_irrigation_mm": 17,
                                    "irrigation_timing": "05:30 - 07:00",
                                }
                            ],
                        },
                        "timeline": [
                            {
                                "step_number": 1,
                                "title": "بررسی فشار",
                                "description": "فشار ابتدا و انتهای لاین کنترل شود",
                            }
                        ],
                        "sections": [
                            {
                                "title": "هشدار تبخیر بالا",
                                "icon": "tabler-alert-triangle",
                                "type": "warning",
                                "content": "در ساعات گرم روز آبیاری انجام نشود",
                            },
                            {
                                "title": "نکته بهره وری",
                                "icon": "tabler-bulb",
                                "type": "tip",
                                "content": "شست وشوی فیلترها به یکنواختی آبیاری کمک می کند",
                            },
                        ],
                    }
                }
            },
        )

        request = self.factory.post(
            "/api/irrigation/recommend/",
            {
                "farm_uuid": str(self.farm.farm_uuid),
                "plant_name": "گوجه فرنگی",
                "growth_stage": "گلدهی",
            },
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = RecommendView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertIn("recommendation_uuid", response.data["data"])
        self.assertEqual(response.data["data"]["status"], IrrigationRecommendationRequest.STATUS_PENDING_CONFIRMATION)
        self.assertEqual(response.data["data"]["status_label"], "منتظر تایید")
        self.assertEqual(IrrigationPlan.objects.count(), 1)
        plan = IrrigationPlan.objects.get()
        self.assertEqual(plan.source, IrrigationPlan.SOURCE_RECOMMENDATION)
        self.assertTrue(plan.is_active)
        self.assertFalse(plan.is_deleted)
        self.assertEqual(response.data["data"]["plan"]["durationMinutes"], 38)
        self.assertEqual(response.data["data"]["water_balance"]["active_kc"], 0.93)
        self.assertEqual(response.data["data"]["timeline"][0]["step_number"], 1)
        self.assertEqual(response.data["data"]["sections"][0]["type"], "warning")
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/irrigation/recommend/",
            method="POST",
            payload={
                "farm_uuid": str(self.farm.farm_uuid),
                "plant_name": "گوجه فرنگی",
                "growth_stage": "گلدهی",
                "irrigation_method_id": 3,
                "irrigation_type": "آبیاری قطره ای",
                "irrigation_method_name": "آبیاری قطره ای",
            },
        )

    @patch("irrigation.views.external_api_request")
    def test_post_includes_active_irrigation_plan_in_ai_payload(self, mock_external_api_request):
        IrrigationPlan.objects.create(
            farm=self.farm,
            source=IrrigationPlan.SOURCE_FREE_TEXT,
            title="برنامه فعال",
            crop_id="گوجه فرنگی",
            growth_stage="گلدهی",
            plan_payload={
                "plan": {"frequencyPerWeek": 2, "durationMinutes": 25, "bestTimeOfDay": "صبح"},
                "water_balance": {"active_kc": 0.82, "daily": []},
                "timeline": [{"step_number": 1, "title": "مرحله", "description": "توضیح"}],
                "sections": [{"type": "warning", "title": "هشدار", "content": "متن"}],
            },
            is_active=True,
        )
        mock_external_api_request.return_value = AdapterResponse(status_code=200, data={"data": {"result": {"plan": {}}}})

        request = self.factory.post(
            "/api/irrigation/recommend/",
            {"farm_uuid": str(self.farm.farm_uuid), "plant_name": "گوجه فرنگی", "growth_stage": "گلدهی"},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = RecommendView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        sent_payload = mock_external_api_request.call_args.kwargs["payload"]
        self.assertIn("active_irrigation_plan", sent_payload)
        self.assertEqual(sent_payload["active_irrigation_plan"]["plan"]["durationMinutes"], 25)
        self.assertEqual(sent_payload["active_irrigation_plan"]["water_balance"]["active_kc"], 0.82)


class IrrigationRecommendationHistoryTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            username="history-farmer",
            password="secret123",
            email="history@example.com",
            phone_number="09120000003",
        )
        self.other_user = get_user_model().objects.create_user(
            username="other-history-farmer",
            password="secret123",
            email="other-history@example.com",
            phone_number="09120000004",
        )
        self.farm_type = FarmType.objects.create(name="گلخانه ای")
        self.farm = FarmHub.objects.create(owner=self.user, farm_type=self.farm_type, name="History Farm")
        self.other_farm = FarmHub.objects.create(owner=self.other_user, farm_type=self.farm_type, name="Other History Farm")

    def test_recommendation_list_returns_paginated_items(self):
        first = IrrigationRecommendationRequest.objects.create(
            farm=self.farm,
            crop_id="گندم",
            growth_stage="vegetative",
            status=IrrigationRecommendationRequest.STATUS_COMPLETED,
            request_payload={"irrigation_method_name": "بارانی"},
            response_payload={"data": {"plan": {"durationMinutes": 20}}},
        )
        second = IrrigationRecommendationRequest.objects.create(
            farm=self.farm,
            crop_id="ذرت",
            growth_stage="flowering",
            status=IrrigationRecommendationRequest.STATUS_PENDING_CONFIRMATION,
            request_payload={"irrigation_method_name": "قطره ای"},
            response_payload={"data": {"plan": {"durationMinutes": 35}}},
        )

        request = self.factory.get(
            f"/api/irrigation/recommendations/?farm_uuid={self.farm.farm_uuid}&page=1&page_size=1"
        )
        force_authenticate(request, user=self.user)

        response = RecommendationListView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["pagination"]["total_items"], 2)
        self.assertEqual(response.data["data"][0]["recommendation_uuid"], str(second.uuid))
        self.assertEqual(response.data["data"][0]["plant_name"], "ذرت")
        self.assertEqual(response.data["data"][0]["growth_stage"], "flowering")
        self.assertEqual(response.data["data"][0]["irrigation_method_name"], "قطره ای")
        self.assertEqual(response.data["data"][0]["status"], IrrigationRecommendationRequest.STATUS_PENDING_CONFIRMATION)
        self.assertEqual(response.data["data"][0]["status_label"], "منتظر تایید")
        self.assertNotEqual(response.data["data"][0]["recommendation_uuid"], str(first.uuid))

    def test_recommendation_detail_returns_saved_shape(self):
        recommendation = IrrigationRecommendationRequest.objects.create(
            farm=self.farm,
            crop_id="گوجه فرنگی",
            growth_stage="fruiting",
            status=IrrigationRecommendationRequest.STATUS_COMPLETED,
            request_payload={"irrigation_method_name": "قطره ای"},
            response_payload={
                "data": {
                    "result": {
                        "plan": {"frequencyPerWeek": 4, "durationMinutes": 30},
                        "water_balance": {"active_kc": 0.93, "daily": []},
                        "timeline": [{"step_number": 1, "title": "مرحله اول", "description": "اجرا شود"}],
                        "sections": [{"type": "tip", "title": "نکته", "content": "صبح زود آبیاری شود"}],
                    }
                }
            },
        )

        request = self.factory.get(f"/api/irrigation/recommendations/{recommendation.uuid}/")
        force_authenticate(request, user=self.user)

        response = RecommendationDetailView.as_view()(request, recommendation_uuid=recommendation.uuid)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(response.data["data"]["recommendation_uuid"], str(recommendation.uuid))
        self.assertEqual(response.data["data"]["crop_id"], "گوجه فرنگی")
        self.assertEqual(response.data["data"]["plant_name"], "گوجه فرنگی")
        self.assertEqual(response.data["data"]["growth_stage"], "fruiting")
        self.assertEqual(response.data["data"]["irrigation_method_name"], "قطره ای")
        self.assertEqual(response.data["data"]["status"], IrrigationRecommendationRequest.STATUS_COMPLETED)
        self.assertEqual(response.data["data"]["status_label"], "پایان یافته")
        self.assertEqual(response.data["data"]["plan"]["durationMinutes"], 30)
        self.assertEqual(response.data["data"]["timeline"][0]["step_number"], 1)
        self.assertEqual(response.data["data"]["sections"][0]["type"], "tip")

    def test_recommendation_detail_rejects_foreign_recommendation(self):
        recommendation = IrrigationRecommendationRequest.objects.create(
            farm=self.other_farm,
            crop_id="خیار",
            status=IrrigationRecommendationRequest.STATUS_PENDING_CONFIRMATION,
        )

        request = self.factory.get(f"/api/irrigation/recommendations/{recommendation.uuid}/")
        force_authenticate(request, user=self.user)

        response = RecommendationDetailView.as_view()(request, recommendation_uuid=recommendation.uuid)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["msg"], "Recommendation not found.")

    @patch("irrigation.views.external_api_request")
    def test_post_accepts_sensor_uuid_as_farm_uuid_alias(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={"data": {"result": {"sections": []}}},
        )

        request = self.factory.post(
            "/api/irrigation/recommend/",
            {
                "sensor_uuid": str(self.farm.farm_uuid),
            },
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = RecommendView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["plan"]["frequencyPerWeek"], 4)
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/irrigation/recommend/",
            method="POST",
            payload={
                "farm_uuid": str(self.farm.farm_uuid),
                "irrigation_method_id": 3,
                "irrigation_type": "آبیاری قطره ای",
                "irrigation_method_name": "آبیاری قطره ای",
            },
        )


class IrrigationPlanApiTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            username="irrigation-plan-user",
            password="secret123",
            email="irrigation-plan@example.com",
            phone_number="09124445566",
        )
        self.farm_type = FarmType.objects.create(name="زراعی")
        self.farm = FarmHub.objects.create(owner=self.user, farm_type=self.farm_type, name="Irrigation Plan Farm")
        self.plan = IrrigationPlan.objects.create(
            farm=self.farm,
            source=IrrigationPlan.SOURCE_FREE_TEXT,
            title="برنامه آبیاری نمونه",
            crop_id="گندم",
            growth_stage="flowering",
            plan_payload={"plan": {"durationMinutes": 25}},
        )

    def test_plan_list_returns_non_deleted_plans(self):
        IrrigationPlan.objects.create(
            farm=self.farm,
            source=IrrigationPlan.SOURCE_RECOMMENDATION,
            title="حذف شده",
            is_deleted=True,
            is_active=False,
        )

        request = self.factory.get(f"/api/irrigation/plans/?farm_uuid={self.farm.farm_uuid}")
        force_authenticate(request, user=self.user)

        response = IrrigationPlanListView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["plan_uuid"], str(self.plan.uuid))

    def test_plan_detail_returns_plan_payload(self):
        request = self.factory.get(f"/api/irrigation/plans/{self.plan.uuid}/")
        force_authenticate(request, user=self.user)

        response = IrrigationPlanDetailView.as_view()(request, plan_uuid=self.plan.uuid)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["plan_uuid"], str(self.plan.uuid))
        self.assertEqual(response.data["data"]["plan_payload"]["plan"]["durationMinutes"], 25)

    def test_plan_delete_is_soft_delete(self):
        request = self.factory.delete(f"/api/irrigation/plans/{self.plan.uuid}/")
        force_authenticate(request, user=self.user)

        response = IrrigationPlanDetailView.as_view()(request, plan_uuid=self.plan.uuid)

        self.assertEqual(response.status_code, 200)
        self.plan.refresh_from_db()
        self.assertTrue(self.plan.is_deleted)
        self.assertFalse(self.plan.is_active)

    def test_plan_status_patch_updates_is_active(self):
        request = self.factory.patch(
            f"/api/irrigation/plans/{self.plan.uuid}/status/",
            {"is_active": False},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = IrrigationPlanStatusView.as_view()(request, plan_uuid=self.plan.uuid)

        self.assertEqual(response.status_code, 200)
        self.plan.refresh_from_db()
        self.assertFalse(self.plan.is_active)
