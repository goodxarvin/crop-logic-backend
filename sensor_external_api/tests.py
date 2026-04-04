from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory

from farm_hub.models import FarmHub, FarmType
from notifications.models import FarmNotification

from .views import SensorExternalAPIView


@override_settings(SENSOR_EXTERNAL_API_KEY="12345")
class SensorExternalAPIViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            username="sensor-external-user",
            password="secret123",
            email="sensor-external@example.com",
            phone_number="09120000015",
        )
        self.farm_type = FarmType.objects.create(name="سنسور خارجی")
        self.farm = FarmHub.objects.create(
            owner=self.user,
            farm_type=self.farm_type,
            name="Farm External",
            farm_uuid="11111111-1111-1111-1111-111111111111",
        )

    def test_requires_api_key(self):
        request = self.factory.post("/api/sensor-external-api/", {"payload": {"temp": 12}}, format="json")

        response = SensorExternalAPIView.as_view()(request)

        self.assertEqual(response.status_code, 401)

    def test_creates_notification_for_fixed_farm_uuid(self):
        request = self.factory.post(
            "/api/sensor-external-api/",
            {"payload": {"temp": 12}},
            format="json",
            HTTP_X_API_KEY="12345",
        )

        response = SensorExternalAPIView.as_view()(request)

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            FarmNotification.objects.filter(
                farm=self.farm,
                title="Sensor external API request",
            ).exists()
        )
