from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate

from external_api_adapter.adapter import AdapterResponse
from farm_hub.models import FarmHub, FarmType, Product
from fertilization.models import FertilizationPlan
from irrigation.models import IrrigationPlan

from .views import (
    CurrentFarmChartView,
    GrowthSimulationStatusView,
    GrowthSimulationView,
    HarvestPredictionView,
    YieldHarvestSummaryView,
    YieldPredictionView,
)


class CropSimulationViewTests(TestCase):
    def setUp(self):
        self.api_client = APIClient()
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
        self.product = Product.objects.create(farm_type=self.farm_type, name="گوجه‌فرنگی")
        self.farm.products.add(self.product)
        self.api_client.force_authenticate(user=self.user)

    @patch("yield_harvest.views.external_api_request")
    def test_growth_queues_simulation_task(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=202,
            data={
                "data": {
                    "task_id": "growth-task-123",
                    "status_url": "/api/crop-simulation/growth/growth-task-123/status/",
                    "plant_name": "گوجه‌فرنگی",
                }
            },
        )

        request = self.factory.post(
            "/api/yield-harvest/crop-simulation/growth/",
            {"plant_name": "گوجه‌فرنگی", "dynamic_parameters": ["DVS", "LAI"], "farm_uuid": str(self.farm.farm_uuid)},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = GrowthSimulationView.as_view()(request)

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data["code"], 202)
        self.assertEqual(response.data["data"]["task_id"], "growth-task-123")
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/crop-simulation/growth/",
            method="POST",
            payload={
                "plant_name": "گوجه‌فرنگی",
                "dynamic_parameters": ["DVS", "LAI"],
                "farm_uuid": str(self.farm.farm_uuid),
            },
        )

    @patch("yield_harvest.views.external_api_request")
    def test_growth_top_level_route_queues_simulation_task(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=202,
            data={
                "data": {
                    "task_id": "growth-task-123",
                    "status_url": "/api/crop-simulation/growth/growth-task-123/status/",
                    "plant_name": "گوجه‌فرنگی",
                }
            },
        )

        response = self.api_client.post(
            "/api/crop-simulation/growth/",
            {
                "plant_name": "گوجه‌فرنگی",
                "dynamic_parameters": ["DVS", "LAI"],
                "farm_uuid": str(self.farm.farm_uuid),
            },
            format="json",
        )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json()["data"]["task_id"], "growth-task-123")

    @patch("yield_harvest.views.external_api_request")
    def test_growth_yield_harvest_route_queues_simulation_task(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=202,
            data={
                "data": {
                    "task_id": "growth-task-123",
                    "status_url": "/api/crop-simulation/growth/growth-task-123/status/",
                    "plant_name": "گوجه‌فرنگی",
                }
            },
        )

        response = self.api_client.post(
            "/api/yield-harvest/growth/",
            {
                "plant_name": "wheat",
                "dynamic_parameters": ["DVS", "LAI"],
                "farm_uuid": str(self.farm.farm_uuid),
            },
            format="json",
        )

        self.assertEqual(response.status_code, 202)
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/crop-simulation/growth/",
            method="POST",
            payload={
                "plant_name": "گوجه‌فرنگی",
                "dynamic_parameters": ["DVS", "LAI"],
                "farm_uuid": str(self.farm.farm_uuid),
            },
        )

    def test_growth_requires_farm_uuid_or_weather(self):
        request = self.factory.post(
            "/api/yield-harvest/crop-simulation/growth/",
            {"plant_name": "گوجه‌فرنگی", "dynamic_parameters": ["DVS"]},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = GrowthSimulationView.as_view()(request)

        self.assertEqual(response.status_code, 400)

    @patch("yield_harvest.views.external_api_request")
    def test_growth_status_proxies_to_ai_service(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={
                "data": {
                    "task_id": "growth-task-123",
                    "status": "SUCCESS",
                    "message": "done",
                    "progress": {},
                    "result": {
                        "plant_name": "گوجه‌فرنگی",
                        "dynamic_parameters": ["DVS", "LAI"],
                        "scenario_id": 1,
                    },
                    "error": "",
                }
            },
        )

        request = self.factory.get("/api/yield-harvest/crop-simulation/growth/growth-task-123/status/?page=1&page_size=10")
        force_authenticate(request, user=self.user)
        response = GrowthSimulationStatusView.as_view()(request, task_id="growth-task-123")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(response.data["data"]["status"], "SUCCESS")
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/crop-simulation/growth/growth-task-123/status/",
            method="GET",
            query={"page": "1", "page_size": "10"},
        )

    @patch("yield_harvest.views.external_api_request")
    def test_growth_status_top_level_route_proxies_to_ai_service(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={
                "data": {
                    "task_id": "growth-task-123",
                    "status": "SUCCESS",
                    "message": "done",
                    "progress": {},
                    "result": {
                        "plant_name": "گوجه‌فرنگی",
                        "dynamic_parameters": ["DVS", "LAI"],
                        "scenario_id": 1,
                    },
                    "error": "",
                }
            },
        )

        response = self.api_client.get("/api/crop-simulation/growth/growth-task-123/status/?page=1&page_size=10")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["status"], "SUCCESS")

    @patch("yield_harvest.views.external_api_request")
    def test_growth_status_yield_harvest_route_proxies_to_ai_service(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={"data": {"task_id": "growth-task-123", "status": "SUCCESS"}},
        )

        response = self.api_client.get("/api/yield-harvest/growth/growth-task-123/status/?page=1&page_size=10")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["status"], "SUCCESS")

    def test_legacy_plant_simulator_routes_are_unavailable(self):
        legacy_paths = [
            "/api/yield-harvest/plant-simulator/config/",
            "/api/yield-harvest/plant-simulator/environment/",
            "/api/yield-harvest/plant-simulator/reset/",
            "/api/yield-harvest/plant-simulator/start/",
            "/api/yield-harvest/plant-simulator/state/",
            "/api/yield-harvest/plant-simulator/stop/",
        ]

        for path in legacy_paths:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 404, path)

    @patch("yield_harvest.views.external_api_request")
    def test_current_farm_chart_proxies_to_ai_service(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={
                "data": {
                    "result": {
                        "farm_uuid": str(self.farm.farm_uuid),
                        "plant_name": "گوجه‌فرنگی",
                        "scenario_id": 1,
                        "categories": ["day1"],
                        "series": {"biomass": [1.2]},
                    }
                }
            },
        )

        request = self.factory.post(
            "/api/yield-harvest/crop-simulation/current-farm-chart/",
            {"farm_uuid": str(self.farm.farm_uuid), "plant_name": "wheat"},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = CurrentFarmChartView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(response.data["data"]["scenario_id"], 1)
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/crop-simulation/current-farm-chart/",
            method="POST",
            payload={"farm_uuid": str(self.farm.farm_uuid), "plant_name": "گوجه‌فرنگی"},
        )

    @patch("yield_harvest.views.external_api_request")
    def test_current_farm_chart_top_level_route_proxies_to_ai_service(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={"data": {"result": {"farm_uuid": str(self.farm.farm_uuid), "plant_name": "wheat"}}},
        )

        response = self.api_client.post(
            "/api/crop-simulation/current-farm-chart/",
            {"farm_uuid": str(self.farm.farm_uuid), "plant_name": "wheat"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["farm_uuid"], str(self.farm.farm_uuid))

    @patch("yield_harvest.views.external_api_request")
    def test_current_farm_chart_yield_harvest_route_proxies_to_ai_service(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={"data": {"result": {"farm_uuid": str(self.farm.farm_uuid), "plant_name": "گوجه‌فرنگی"}}},
        )

        response = self.api_client.post(
            "/api/yield-harvest/current-farm-chart/",
            {"farm_uuid": str(self.farm.farm_uuid), "plant_name": "wheat"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/crop-simulation/current-farm-chart/",
            method="POST",
            payload={"farm_uuid": str(self.farm.farm_uuid), "plant_name": "گوجه‌فرنگی"},
        )

    @patch("yield_harvest.views.external_api_request")
    def test_harvest_prediction_proxies_to_ai_service(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={
                "data": {
                    "result": {
                        "date": "2026-07-15",
                        "dateFormatted": "15 Jul 2026",
                        "daysUntil": 96,
                        "gddDetails": {"current": 800},
                    }
                }
            },
        )

        request = self.factory.post(
            "/api/yield-harvest/crop-simulation/harvest-prediction/",
            {"farm_uuid": str(self.farm.farm_uuid)},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = HarvestPredictionView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["daysUntil"], 96)
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/crop-simulation/harvest-prediction/",
            method="POST",
            payload={"farm_uuid": str(self.farm.farm_uuid), "plant_name": "گوجه‌فرنگی"},
        )

    @patch("yield_harvest.views.external_api_request")
    def test_harvest_prediction_top_level_route_proxies_to_ai_service(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={"data": {"result": {"date": "2026-07-15", "daysUntil": 96}}},
        )

        response = self.api_client.post(
            "/api/crop-simulation/harvest-prediction/",
            {"farm_uuid": str(self.farm.farm_uuid)},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["daysUntil"], 96)

    @patch("yield_harvest.views.external_api_request")
    def test_harvest_prediction_yield_harvest_route_proxies_to_ai_service(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={"data": {"result": {"date": "2026-07-15", "daysUntil": 96}}},
        )

        response = self.api_client.post(
            "/api/yield-harvest/harvest-prediction/",
            {"farm_uuid": str(self.farm.farm_uuid)},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/crop-simulation/harvest-prediction/",
            method="POST",
            payload={"farm_uuid": str(self.farm.farm_uuid), "plant_name": "گوجه‌فرنگی"},
        )

    @patch("yield_harvest.views.external_api_request")
    def test_current_farm_chart_includes_selected_plans(self, mock_external_api_request):
        irrigation_plan = IrrigationPlan.objects.create(
            farm=self.farm,
            source=IrrigationPlan.SOURCE_FREE_TEXT,
            title="برنامه آبیاری",
            plan_payload={"plan": {"durationMinutes": 20}},
        )
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={"data": {"result": {"farm_uuid": str(self.farm.farm_uuid), "series": []}}},
        )

        response = self.api_client.post(
            "/api/yield-harvest/current-farm-chart/",
            {"farm_uuid": str(self.farm.farm_uuid), "irrigation_plan_id": irrigation_plan.id},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        sent_payload = mock_external_api_request.call_args.kwargs["payload"]
        self.assertEqual(sent_payload["irrigation_plan"]["id"], irrigation_plan.id)

    @patch("yield_harvest.views.external_api_request")
    def test_harvest_prediction_includes_selected_plans(self, mock_external_api_request):
        fertilization_plan = FertilizationPlan.objects.create(
            farm=self.farm,
            source=FertilizationPlan.SOURCE_FREE_TEXT,
            title="برنامه کودی",
            plan_payload={"primary_recommendation": {"fertilizer_code": "npk-151515"}},
        )
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={"data": {"result": {"date": "2026-07-15", "daysUntil": 96}}},
        )

        response = self.api_client.post(
            "/api/yield-harvest/harvest-prediction/",
            {"farm_uuid": str(self.farm.farm_uuid), "fertilization_plan_id": fertilization_plan.id},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        sent_payload = mock_external_api_request.call_args.kwargs["payload"]
        self.assertEqual(sent_payload["fertilization_plan"]["id"], fertilization_plan.id)

    @patch("yield_harvest.views.external_api_request")
    def test_yield_prediction_proxies_to_ai_service(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={
                "data": {
                    "result": {
                        "farm_uuid": str(self.farm.farm_uuid),
                        "predictedYieldTons": 8.4,
                        "scenarioId": 1,
                    }
                }
            },
        )

        request = self.factory.post(
            "/api/yield-harvest/crop-simulation/yield-prediction/",
            {"farm_uuid": str(self.farm.farm_uuid)},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = YieldPredictionView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["predictedYieldTons"], 8.4)
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/crop-simulation/yield-prediction/",
            method="POST",
            payload={"farm_uuid": str(self.farm.farm_uuid), "plant_name": "گوجه‌فرنگی"},
        )

    @patch("yield_harvest.views.external_api_request")
    def test_yield_prediction_top_level_route_proxies_to_ai_service(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={"data": {"result": {"farm_uuid": str(self.farm.farm_uuid), "predictedYieldTons": 8.4}}},
        )

        response = self.api_client.post(
            "/api/crop-simulation/yield-prediction/",
            {"farm_uuid": str(self.farm.farm_uuid)},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["predictedYieldTons"], 8.4)

    @patch("yield_harvest.views.external_api_request")
    def test_yield_prediction_yield_harvest_route_proxies_to_ai_service(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={"data": {"result": {"farm_uuid": str(self.farm.farm_uuid), "predictedYieldTons": 8.4}}},
        )

        response = self.api_client.post(
            "/api/yield-harvest/yield-prediction/",
            {"farm_uuid": str(self.farm.farm_uuid)},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/crop-simulation/yield-prediction/",
            method="POST",
            payload={"farm_uuid": str(self.farm.farm_uuid), "plant_name": "گوجه‌فرنگی"},
        )

    @patch("yield_harvest.views.external_api_request")
    def test_yield_prediction_falls_back_to_farm_type_product_when_farm_products_are_empty(self, mock_external_api_request):
        farm_without_products = FarmHub.objects.create(owner=self.user, farm_type=self.farm_type, name="Farm fallback")
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={"data": {"result": {"farm_uuid": str(farm_without_products.farm_uuid), "predictedYieldTons": 8.4}}},
        )

        response = self.api_client.post(
            "/api/yield-harvest/yield-prediction/",
            {"farm_uuid": str(farm_without_products.farm_uuid)},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/crop-simulation/yield-prediction/",
            method="POST",
            payload={"farm_uuid": str(farm_without_products.farm_uuid), "plant_name": "گوجه‌فرنگی"},
        )

    @patch("yield_harvest.views.external_api_request")
    def test_yield_prediction_includes_selected_irrigation_and_fertilization_plans(self, mock_external_api_request):
        irrigation_plan = IrrigationPlan.objects.create(
            farm=self.farm,
            source=IrrigationPlan.SOURCE_FREE_TEXT,
            title="برنامه آبیاری",
            crop_id="گوجه‌فرنگی",
            growth_stage="flowering",
            plan_payload={"plan": {"durationMinutes": 30}},
            request_payload={"source": "manual"},
            response_payload={"ok": True},
        )
        fertilization_plan = FertilizationPlan.objects.create(
            farm=self.farm,
            source=FertilizationPlan.SOURCE_FREE_TEXT,
            title="برنامه کودی",
            crop_id="گوجه‌فرنگی",
            growth_stage="flowering",
            plan_payload={"primary_recommendation": {"fertilizer_code": "npk-202020"}},
            request_payload={"source": "manual"},
            response_payload={"ok": True},
        )
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={"data": {"result": {"farm_uuid": str(self.farm.farm_uuid), "predictedYieldTons": 8.4}}},
        )

        response = self.api_client.post(
            "/api/yield-harvest/yield-prediction/",
            {
                "farm_uuid": str(self.farm.farm_uuid),
                "irrigation_plan_id": irrigation_plan.id,
                "fertilization_plan_id": fertilization_plan.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        sent_payload = mock_external_api_request.call_args.kwargs["payload"]
        self.assertEqual(sent_payload["irrigation_plan"]["id"], irrigation_plan.id)
        self.assertEqual(sent_payload["irrigation_plan"]["plan_payload"]["plan"]["durationMinutes"], 30)
        self.assertEqual(sent_payload["fertilization_plan"]["id"], fertilization_plan.id)
        self.assertEqual(
            sent_payload["fertilization_plan"]["plan_payload"]["primary_recommendation"]["fertilizer_code"],
            "npk-202020",
        )

    def test_yield_prediction_rejects_foreign_plan_ids(self):
        other_irrigation_plan = IrrigationPlan.objects.create(
            farm=self.other_farm,
            source=IrrigationPlan.SOURCE_FREE_TEXT,
            title="other irrigation",
        )

        response = self.api_client.post(
            "/api/yield-harvest/yield-prediction/",
            {
                "farm_uuid": str(self.farm.farm_uuid),
                "irrigation_plan_id": other_irrigation_plan.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["data"]["irrigation_plan_id"][0], "Irrigation plan not found.")

    @patch("yield_harvest.views.external_api_request")
    def test_yield_harvest_summary_top_level_route_proxies_to_ai_service(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={
                "data": {
                    "result": {
                        "farm_uuid": str(self.farm.farm_uuid),
                        "season_highlights_card": {"title": "Season highlights"},
                        "yield_prediction": {"predicted_yield_tons": 5.1},
                        "harvest_prediction_card": {"harvest_date": "2026-09-28", "days_until": 152},
                        "harvest_readiness_zones": {"zones": []},
                        "yield_quality_bands": {"primary_quality_grade": "B"},
                        "harvest_operations_card": {"steps": []},
                        "yield_prediction_chart": {"series": []},
                    }
                }
            },
        )

        response = self.api_client.get(
            f"/api/crop-simulation/yield-harvest-summary/?farm_uuid={self.farm.farm_uuid}&season_year=1404&crop_name=wheat&include_narrative=true"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["farm_uuid"], str(self.farm.farm_uuid))
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/crop-simulation/yield-harvest-summary/",
            method="GET",
            query={
                "farm_uuid": str(self.farm.farm_uuid),
                "season_year": "1404",
                "crop_name": "wheat",
                "include_narrative": "true",
            },
        )

    @patch("yield_harvest.views.external_api_request")
    def test_yield_harvest_summary_yield_harvest_route_proxies_to_ai_service(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={"data": {"result": {"farm_uuid": str(self.farm.farm_uuid), "yield_prediction_chart": {"series": []}}}},
        )

        response = self.api_client.get(f"/api/yield-harvest/yield-harvest-summary/?farm_uuid={self.farm.farm_uuid}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["farm_uuid"], str(self.farm.farm_uuid))

    @patch("yield_harvest.views.external_api_request")
    def test_yield_harvest_summary_includes_selected_plans_in_query(self, mock_external_api_request):
        irrigation_plan = IrrigationPlan.objects.create(
            farm=self.farm,
            source=IrrigationPlan.SOURCE_FREE_TEXT,
            title="برنامه آبیاری",
            plan_payload={"plan": {"durationMinutes": 18}},
        )
        fertilization_plan = FertilizationPlan.objects.create(
            farm=self.farm,
            source=FertilizationPlan.SOURCE_FREE_TEXT,
            title="برنامه کودی",
            plan_payload={"primary_recommendation": {"fertilizer_code": "npk-111111"}},
        )
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={"data": {"result": {"farm_uuid": str(self.farm.farm_uuid), "yield_prediction_chart": {"series": []}}}},
        )

        response = self.api_client.get(
            f"/api/yield-harvest/yield-harvest-summary/?farm_uuid={self.farm.farm_uuid}&irrigation_plan_id={irrigation_plan.id}&fertilization_plan_id={fertilization_plan.id}"
        )

        self.assertEqual(response.status_code, 200)
        sent_query = mock_external_api_request.call_args.kwargs["query"]
        self.assertEqual(sent_query["irrigation_plan"]["id"], irrigation_plan.id)
        self.assertEqual(sent_query["fertilization_plan"]["id"], fertilization_plan.id)

    def test_crop_simulation_rejects_foreign_farm_uuid(self):
        request = self.factory.post(
            "/api/yield-harvest/crop-simulation/yield-prediction/",
            {"farm_uuid": str(self.other_farm.farm_uuid)},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = YieldPredictionView.as_view()(request)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["code"], 404)
        self.assertEqual(response.data["data"]["farm_uuid"][0], "Farm not found.")
