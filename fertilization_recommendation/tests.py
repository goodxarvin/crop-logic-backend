from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from unittest.mock import patch

from external_api_adapter.adapter import AdapterResponse
from farm_hub.models import FarmHub, FarmType
from .views import RecommendView


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

    @patch("fertilization_recommendation.views.external_api_request")
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
            {"farm_uuid": str(self.farm.farm_uuid), "plant_name": "گندم", "growth_stage": "vegetative"},
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
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/fertilization/recommend/",
            method="POST",
            payload={
                "farm_uuid": str(self.farm.farm_uuid),
                "plant_name": "گندم",
                "growth_stage": "vegetative",
            },
        )
