import uuid

from django.db import transaction

from account.seeds import seed_admin_user

from .models import Sensor
from .services import dispatch_sensor_zoning


ADMIN_SENSOR_UUID = uuid.UUID("11111111-1111-1111-1111-111111111111")
ADMIN_SENSOR_DATA = {
    "name": "Admin Smart Farm Sensor",
    "is_active": True,
    "specifications": {
        "model": "CL-SENSE-PRO-X",
        "firmware": "2.4.1",
        "manufacturer": "CropLogic",
        "serial_number": "CL-ADMIN-0001",
        "capabilities": [
            "temperature",
            "humidity",
            "soil_moisture",
            "soil_temperature",
            "light_intensity",
            "ph",
            "ec",
            "wind_speed",
        ],
        "connectivity": {
            "protocol": "LoRaWAN",
            "sim_enabled": True,
            "bluetooth": True,
            "wifi_fallback": True,
        },
        "location": {
            "label": "Admin Demo Field",
            "lat": 35.6892,
            "lng": 51.389,
            "altitude_m": 1190,
        },
    },
    "power_source": {
        "type": "hybrid",
        "battery": {
            "capacity_mah": 12000,
            "voltage": 12,
            "health_percent": 98,
        },
        "solar": {
            "panel_watt": 40,
            "controller": "MPPT",
        },
        "backup": "dc_adapter",
    },
    "customized_sensors": {
        "thresholds": {
            "temperature_c": {"min": 10, "max": 36},
            "humidity_percent": {"min": 30, "max": 85},
            "soil_moisture_percent": {"min": 25, "max": 70},
            "ph": {"min": 5.8, "max": 7.2},
            "ec_ds_m": {"min": 1.1, "max": 2.4},
        },
        "report_interval_sec": 300,
        "alerts": {
            "sms": True,
            "email": True,
            "push": True,
        },
        "calibration": {
            "last_calibrated_at": "2025-03-01T08:30:00Z",
            "technician": "system",
            "status": "passed",
        },
    },
}

ADMIN_SENSOR_AREA_GEOJSON = {
    "type": "Feature",
    "properties": {},
    "geometry": {
        "type": "Polygon",
        "coordinates": [
            [
                [51.418934, 35.706815],
                [51.423054, 35.691062],
                [51.384258, 35.689389],
                [51.418934, 35.706815],
            ]
        ],
    },
}


@transaction.atomic
def seed_admin_sensor():
    owner, _ = seed_admin_user()
    sensor, created = Sensor.objects.update_or_create(
        uuid_sensor=ADMIN_SENSOR_UUID,
        defaults={
            "owner": owner,
            "name": ADMIN_SENSOR_DATA["name"],
            "is_active": ADMIN_SENSOR_DATA["is_active"],
            "specifications": ADMIN_SENSOR_DATA["specifications"],
            "power_source": ADMIN_SENSOR_DATA["power_source"],
            "customized_sensors": ADMIN_SENSOR_DATA["customized_sensors"],
        },
    )
    if created:
        dispatch_sensor_zoning(ADMIN_SENSOR_AREA_GEOJSON)
    return sensor, created
