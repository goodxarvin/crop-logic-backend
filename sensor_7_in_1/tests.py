from datetime import datetime, timedelta, timezone as dt_timezone

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory, force_authenticate

from farm_hub.models import FarmHub, FarmSensor, FarmType
from sensor_catalog.models import SensorCatalog
from sensor_external_api.models import SensorExternalRequestLog

from dashboard.services import get_farm_dashboard_cards

from .seeds import seed_sensor_7_in_1_demo_data
from .services import (
    get_sensor_7_in_1_summary_data,
    get_sensor_comparison_chart_data,
    get_primary_soil_sensor,
    get_sensor_radar_chart_data,
    get_sensor_values_list_data,
)
from .views import (
    Sensor7In1SummaryView,
    SensorComparisonChartView,
    SensorRadarChartView,
    SensorValuesListView,
)


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
        self.chart_sensor = FarmSensor.objects.create(
            farm=self.farm,
            sensor_catalog=self.sensor_catalog,
            physical_device_uuid="44444444-4444-4444-4444-444444444444",
            name="Comparison Sensor 7-in-1",
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
        now_utc = datetime.now(dt_timezone.utc)
        base_time = now_utc.replace(hour=12, minute=0, second=0, microsecond=0)
        for index, moisture in enumerate([56, 58, 55, 60, 62, 61, 59]):
            log = SensorExternalRequestLog.objects.create(
                farm_uuid=self.farm.farm_uuid,
                sensor_catalog_uuid=self.sensor_catalog.uuid,
                physical_device_uuid=self.chart_sensor.physical_device_uuid,
                payload={
                    "moisture": moisture,
                    "temperature": round(26.2 + (index * 0.2), 1),
                    "humidity": 50 + index,
                },
            )
            SensorExternalRequestLog.objects.filter(id=log.id).update(
                created_at=base_time - timedelta(days=6 - index)
            )


class Sensor7In1ServiceTests(Sensor7In1BaseTestCase):
    def test_primary_sensor_prefers_7_in_1_sensor_over_generic_soil_probe(self):
        sensor = get_primary_soil_sensor(farm=self.farm)

        self.assertEqual(sensor.id, self.sensor.id)
        self.assertEqual(str(sensor.physical_device_uuid), str(self.sensor.physical_device_uuid))

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

    def test_comparison_chart_service_returns_raw_chart_data(self):
        data = get_sensor_comparison_chart_data(
            farm=self.farm,
            physical_device_uuid=self.sensor.physical_device_uuid,
            range_value="7d",
        )

        self.assertEqual(data["series"][0]["name"], "moisture")
        self.assertEqual(data["series"][0]["data"], [41.0, 48.5])
        self.assertEqual(data["currentValue"], 48.5)
        self.assertEqual(data["vsLastWeek"], "+18.3%")
        self.assertEqual(len(data["categories"]), 2)

    def test_values_list_service_returns_formatted_sensor_items(self):
        data = get_sensor_values_list_data(
            farm=self.farm,
            physical_device_uuid=self.sensor.physical_device_uuid,
            range_value="7d",
        )

        self.assertEqual(data["sensors"][0]["title"], "Moisture")
        self.assertEqual(data["sensors"][0]["subtitle"], "مقدار فعلی: 48.5%")
        self.assertEqual(data["sensors"][0]["trendNumber"], 7.5)
        self.assertEqual(data["sensors"][0]["trend"], "positive")
        self.assertEqual(data["sensors"][1]["title"], "Temperature")
        self.assertEqual(data["sensors"][1]["subtitle"], "مقدار فعلی: 23.2°C")
        self.assertEqual(data["sensors"][1]["trend"], "positive")

    def test_radar_chart_service_returns_aligned_labels_and_series(self):
        data = get_sensor_radar_chart_data(
            farm=self.farm,
            physical_device_uuid=self.sensor.physical_device_uuid,
            range_value="7d",
        )

        self.assertEqual(
            data["labels"],
            ["Moisture", "Temperature", "PH", "EC", "Nitrogen", "Potassium"],
        )
        self.assertEqual(data["series"][0]["name"], "وضعیت فعلی")
        self.assertEqual(data["series"][0]["data"], [48.5, 23.2, 6.8, 1.4, 31.0, 24.0])
        self.assertEqual(data["series"][1]["name"], "بازه ایده آل")
        self.assertEqual(data["series"][1]["data"], [60.0, 26.0, 6.5, 1.3, 42.0, 38.0])
        self.assertEqual(len(data["labels"]), len(data["series"][0]["data"]))
        self.assertEqual(len(data["labels"]), len(data["series"][1]["data"]))


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

    def test_sensor_comparison_chart_view_returns_raw_payload(self):
        request = self.factory.get(
            (
                "/api/sensors/comparison-chart/"
                f"?farm_uuid={self.farm.farm_uuid}"
            )
        )
        force_authenticate(request, user=self.user)

        response = SensorComparisonChartView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn("series", response.data)
        self.assertNotIn("code", response.data)
        self.assertEqual(response.data["currentValue"], 48.5)
        self.assertEqual(response.data["vsLastWeek"], "+18.3%")

    def test_sensor_values_list_view_returns_raw_payload(self):
        request = self.factory.get(
            (
                "/api/sensors/values-list/"
                f"?farm_uuid={self.farm.farm_uuid}"
            )
        )
        force_authenticate(request, user=self.user)

        response = SensorValuesListView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["sensors"][0]["title"], "Moisture")
        self.assertEqual(response.data["sensors"][0]["trendNumber"], 7.5)
        self.assertEqual(response.data["sensors"][0]["trend"], "positive")

    def test_sensor_radar_chart_view_returns_raw_payload(self):
        request = self.factory.get(
            (
                "/api/sensors/radar-chart/"
                f"?farm_uuid={self.farm.farm_uuid}"
            )
        )
        force_authenticate(request, user=self.user)

        response = SensorRadarChartView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["labels"], ["Moisture", "Temperature", "PH", "EC", "Nitrogen", "Potassium"])
        self.assertEqual(response.data["series"][0]["name"], "وضعیت فعلی")
        self.assertEqual(response.data["series"][1]["name"], "بازه ایده آل")
        self.assertEqual(len(response.data["labels"]), len(response.data["series"][0]["data"]))


@override_settings(
    USE_EXTERNAL_API_MOCK=True,
    CROP_ZONE_CHUNK_AREA_SQM=200000,
)
class Sensor7In1SeedTests(TestCase):
    def test_seed_sensor_7_in_1_demo_data_creates_idempotent_sensor_logs(self):
        first_result = seed_sensor_7_in_1_demo_data()
        second_result = seed_sensor_7_in_1_demo_data()

        sensor = second_result["sensor"]
        logs = SensorExternalRequestLog.objects.filter(
            farm_uuid=second_result["farm"].farm_uuid,
            physical_device_uuid=sensor.physical_device_uuid,
        )

        self.assertTrue(SensorCatalog.objects.filter(code="sensor-7-in-1").exists())
        self.assertEqual(first_result["farm"].id, second_result["farm"].id)
        self.assertEqual(first_result["sensor"].id, second_result["sensor"].id)
        self.assertEqual(logs.count(), 7)
        self.assertEqual(logs.first().payload["soil_moisture"], 52.4)
