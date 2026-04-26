from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from farm_hub.models import FarmHub, FarmSensor, FarmType
from sensor_catalog.models import SensorCatalog
from sensor_external_api.models import SensorExternalRequestLog

from dashboard.services import get_farm_dashboard_cards

from .services import get_sensor_7_in_1_summary_data
from .views import Sensor7In1ComparisonChartView, Sensor7In1RadarChartView, Sensor7In1SummaryView


class Sensor7In1BaseTestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            username="sensor-7-in-1-user",
            password="secret123",
            email="sensor7@example.com",
            phone_number="09120000017",
        )
        self.farm_type = FarmType.objects.create(name="مزرعه سنسور 7 در 1")
        self.farm = FarmHub.objects.create(
            owner=self.user,
            farm_type=self.farm_type,
            name="Farm Sensor 7 in 1",
            farm_uuid="11111111-1111-1111-1111-111111111111",
        )
        self.sensor_catalog = SensorCatalog.objects.create(
            code="sensor-7-in-1",
            name="7 in 1 Soil Sensor",
            returned_data_fields=[
                "soil_moisture",
                "soil_temperature",
                "soil_ph",
                "electrical_conductivity",
                "nitrogen",
                "phosphorus",
                "potassium",
            ],
        )
        self.sensor = FarmSensor.objects.create(
            farm=self.farm,
            sensor_catalog=self.sensor_catalog,
            physical_device_uuid="33333333-3333-3333-3333-333333333333",
            name="Soil Sensor 7-in-1",
            sensor_type="soil_7_in_1",
        )
        SensorExternalRequestLog.objects.create(
            farm_uuid=self.farm.farm_uuid,
            sensor_catalog_uuid=self.sensor_catalog.uuid,
            physical_device_uuid=self.sensor.physical_device_uuid,
            payload={
                "soil_moisture": 41.0,
                "soil_temperature": 21.0,
                "soil_ph": 6.5,
                "electrical_conductivity": 1.0,
                "nitrogen": 28.0,
                "phosphorus": 14.0,
                "potassium": 19.0,
            },
        )
        self.latest_log = SensorExternalRequestLog.objects.create(
            farm_uuid=self.farm.farm_uuid,
            sensor_catalog_uuid=self.sensor_catalog.uuid,
            physical_device_uuid=self.sensor.physical_device_uuid,
            payload={
                "soil_moisture": 48.5,
                "soil_temperature": 23.2,
                "soil_ph": 6.8,
                "electrical_conductivity": 1.4,
                "nitrogen": 31.0,
                "phosphorus": 16.0,
                "potassium": 24.0,
            },
        )


class Sensor7In1ServiceTests(Sensor7In1BaseTestCase):
    def test_summary_returns_latest_specific_sensor_data(self):
        data = get_sensor_7_in_1_summary_data(self.farm)

        self.assertEqual(data["sensor"]["name"], "Soil Sensor 7-in-1")
        self.assertEqual(data["sensor"]["physicalDeviceUuid"], str(self.sensor.physical_device_uuid))
        self.assertEqual(data["sensorValuesList"]["sensors"][0]["id"], "soil_moisture")
        self.assertEqual(data["avgSoilMoisture"]["stats"], "48.5%")
        self.assertEqual(data["sensorComparisonChart"]["currentValue"], 48.5)
        self.assertEqual(data["soilMoistureHeatmap"]["series"][0]["name"], "Soil Sensor 7-in-1")

    def test_dashboard_cards_use_sensor_service_outputs(self):
        cards = get_farm_dashboard_cards(self.farm)

        self.assertEqual(cards["sensorValuesList"]["sensor"]["physicalDeviceUuid"], str(self.sensor.physical_device_uuid))
        self.assertEqual(cards["sensorValuesList"]["sensors"][0]["title"], "48.5%")
        self.assertEqual(cards["sensorRadarChart"]["series"][0]["name"], "اکنون")
        self.assertEqual(cards["soilMoistureHeatmap"]["series"][0]["name"], "Soil Sensor 7-in-1")
        self.assertEqual(cards["farmOverviewKpis"]["kpis"][2]["stats"], "48.5%")


class Sensor7In1ViewTests(Sensor7In1BaseTestCase):
    def test_summary_view_returns_sensor_cards(self):
        request = self.factory.get(f"/api/sensor-7-in-1/summary/?farm_uuid={self.farm.farm_uuid}")
        force_authenticate(request, user=self.user)

        response = Sensor7In1SummaryView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(response.data["data"]["sensor"]["sensorCatalogCode"], "sensor-7-in-1")

    def test_summary_view_requires_farm_uuid(self):
        request = self.factory.get("/api/sensor-7-in-1/summary/")
        force_authenticate(request, user=self.user)

        response = Sensor7In1SummaryView.as_view()(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["farm_uuid"][0], "This field is required.")

    def test_radar_chart_view_returns_sensor_chart(self):
        request = self.factory.get(f"/api/sensor-7-in-1/sensor-radar-chart/?farm_uuid={self.farm.farm_uuid}")
        force_authenticate(request, user=self.user)

        response = Sensor7In1RadarChartView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(response.data["data"]["series"][0]["name"], "اکنون")

    def test_comparison_chart_view_returns_sensor_chart(self):
        request = self.factory.get(f"/api/sensor-7-in-1/sensor-comparison-chart/?farm_uuid={self.farm.farm_uuid}")
        force_authenticate(request, user=self.user)

        response = Sensor7In1ComparisonChartView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(response.data["data"]["currentValue"], 48.5)
