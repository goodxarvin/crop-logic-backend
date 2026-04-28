from datetime import timedelta
import uuid

from django.db import transaction
from django.utils import timezone

from farm_hub.models import FarmSensor
from farm_hub.seeds import seed_admin_farm
from sensor_catalog.models import SensorCatalog
from sensor_external_api.models import SensorExternalRequestLog


SENSOR_7_IN_1_CATALOG_CODE = "sensor-7-in-1"
SENSOR_7_IN_1_DEVICE_UUID = uuid.UUID("77777777-7777-7777-7777-777777777777")
SENSOR_7_IN_1_LOG_SERIES = [
    {
        "days_ago": 6,
        "payload": {
            "soil_moisture": 44.0,
            "soil_temperature": 20.6,
            "soil_ph": 6.3,
            "electrical_conductivity": 1.0,
            "nitrogen": 25.0,
            "phosphorus": 13.0,
            "potassium": 21.0,
        },
    },
    {
        "days_ago": 5,
        "payload": {
            "soil_moisture": 45.5,
            "soil_temperature": 21.1,
            "soil_ph": 6.4,
            "electrical_conductivity": 1.1,
            "nitrogen": 26.0,
            "phosphorus": 13.8,
            "potassium": 21.8,
        },
    },
    {
        "days_ago": 4,
        "payload": {
            "soil_moisture": 46.8,
            "soil_temperature": 21.7,
            "soil_ph": 6.5,
            "electrical_conductivity": 1.1,
            "nitrogen": 27.4,
            "phosphorus": 14.2,
            "potassium": 22.5,
        },
    },
    {
        "days_ago": 3,
        "payload": {
            "soil_moisture": 48.2,
            "soil_temperature": 22.0,
            "soil_ph": 6.6,
            "electrical_conductivity": 1.2,
            "nitrogen": 28.9,
            "phosphorus": 15.1,
            "potassium": 23.3,
        },
    },
    {
        "days_ago": 2,
        "payload": {
            "soil_moisture": 49.6,
            "soil_temperature": 22.4,
            "soil_ph": 6.6,
            "electrical_conductivity": 1.2,
            "nitrogen": 29.7,
            "phosphorus": 15.7,
            "potassium": 24.1,
        },
    },
    {
        "days_ago": 1,
        "payload": {
            "soil_moisture": 50.9,
            "soil_temperature": 22.8,
            "soil_ph": 6.7,
            "electrical_conductivity": 1.3,
            "nitrogen": 30.8,
            "phosphorus": 16.2,
            "potassium": 24.8,
        },
    },
    {
        "days_ago": 0,
        "payload": {
            "soil_moisture": 52.4,
            "soil_temperature": 23.1,
            "soil_ph": 6.8,
            "electrical_conductivity": 1.3,
            "nitrogen": 32.0,
            "phosphorus": 16.8,
            "potassium": 25.6,
        },
    },
]


def seed_sensor_7_in_1_catalog():
    sensor_catalog, created = SensorCatalog.objects.update_or_create(
        code=SENSOR_7_IN_1_CATALOG_CODE,
        defaults={
            "name": "Sensor 7 in 1 Soil Sensor",
            "description": "Demo 7 in 1 soil sensor for dashboard summary and chart endpoints.",
            "customizable_fields": [],
            "supported_power_sources": ["solar", "battery", "direct_power"],
            "returned_data_fields": [
                "soil_moisture",
                "soil_temperature",
                "soil_ph",
                "electrical_conductivity",
                "nitrogen",
                "phosphorus",
                "potassium",
            ],
            "sample_payload": SENSOR_7_IN_1_LOG_SERIES[-1]["payload"],
            "is_active": True,
        },
    )
    return sensor_catalog, created


@transaction.atomic
def seed_sensor_7_in_1_demo_data():
    farm, _ = seed_admin_farm()
    sensor_catalog, catalog_created = seed_sensor_7_in_1_catalog()

    sensor, sensor_created = FarmSensor.objects.update_or_create(
        farm=farm,
        physical_device_uuid=SENSOR_7_IN_1_DEVICE_UUID,
        defaults={
            "sensor_catalog": sensor_catalog,
            "name": "Sensor 7 in 1 Demo",
            "sensor_type": "soil_7_in_1",
            "is_active": True,
            "specifications": {
                "capabilities": sensor_catalog.returned_data_fields,
                "demo_seed": True,
            },
            "power_source": {"type": "solar"},
        },
    )

    SensorExternalRequestLog.objects.filter(
        farm_uuid=farm.farm_uuid,
        physical_device_uuid=sensor.physical_device_uuid,
    ).delete()

    base_time = timezone.now().replace(hour=12, minute=0, second=0, microsecond=0)
    created_logs = []
    for item in SENSOR_7_IN_1_LOG_SERIES:
        log = SensorExternalRequestLog.objects.create(
            farm_uuid=farm.farm_uuid,
            sensor_catalog_uuid=sensor_catalog.uuid,
            physical_device_uuid=sensor.physical_device_uuid,
            payload=item["payload"],
        )
        created_at = base_time - timedelta(days=item["days_ago"])
        SensorExternalRequestLog.objects.filter(id=log.id).update(created_at=created_at)
        log.created_at = created_at
        created_logs.append(log)

    return {
        "farm": farm,
        "sensor_catalog": sensor_catalog,
        "sensor": sensor,
        "catalog_created": catalog_created,
        "sensor_created": sensor_created,
        "log_count": len(created_logs),
    }
