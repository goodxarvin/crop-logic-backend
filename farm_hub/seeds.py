import uuid

from django.db import transaction

from account.seeds import seed_admin_user

from .models import FarmHub, FarmType, Product
from .services import dispatch_farm_zoning


ADMIN_FARM_UUID = uuid.UUID("11111111-1111-1111-1111-111111111111")
ADMIN_FARM_DATA = {
    "name": "Admin Smart Farm",
    "is_active": True,
    "customization": {
        "irrigation": {
            "mode": "smart",
            "report_interval_sec": 300,
        },
        "alerts": {
            "sms": True,
            "email": True,
            "push": True,
        },
    },
    "sensors": [
        {
            "name": "Station 1",
            "sensor_type": "weather_station",
            "is_active": True,
            "specifications": {
                "model": "CL-SENSE-PRO-X",
                "firmware": "2.4.1",
                "manufacturer": "CropLogic",
            },
            "power_source": {
                "type": "hybrid",
                "battery": {"capacity_mah": 12000, "voltage": 12},
                "solar": {"panel_watt": 40, "controller": "MPPT"},
            },
            "customization": {
                "thresholds": {
                    "temperature_c": {"min": 10, "max": 36},
                    "humidity_percent": {"min": 30, "max": 85},
                }
            },
        },
        {
            "name": "Soil Probe 1",
            "sensor_type": "soil_probe",
            "is_active": True,
            "specifications": {
                "capabilities": ["soil_moisture", "soil_temperature", "ph", "ec"],
            },
            "power_source": {"type": "battery", "backup": "solar"},
            "customization": {
                "depth_cm": [20, 40],
                "thresholds": {
                    "soil_moisture_percent": {"min": 25, "max": 70},
                    "ph": {"min": 5.8, "max": 7.2},
                },
            },
        },
    ],
}

ADMIN_FARM_AREA_GEOJSON = {
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


def _get_default_catalog():
    farm_type, _ = FarmType.objects.get_or_create(name="زراعی")
    wheat, _ = Product.objects.get_or_create(farm_type=farm_type, name="گندم")
    corn, _ = Product.objects.get_or_create(farm_type=farm_type, name="ذرت")
    return farm_type, [wheat, corn]


@transaction.atomic
def seed_admin_farm():
    owner, _ = seed_admin_user()
    farm_type, products = _get_default_catalog()
    farm, created = FarmHub.objects.update_or_create(
        farm_uuid=ADMIN_FARM_UUID,
        defaults={
            "owner": owner,
            "farm_type": farm_type,
            "name": ADMIN_FARM_DATA["name"],
            "is_active": ADMIN_FARM_DATA["is_active"],
            "customization": ADMIN_FARM_DATA["customization"],
        },
    )
    farm.products.set(products)
    farm.sensors.all().delete()
    farm.sensors.bulk_create([farm.sensors.model(farm=farm, **sensor_data) for sensor_data in ADMIN_FARM_DATA["sensors"]])
    if created:
        dispatch_farm_zoning(ADMIN_FARM_AREA_GEOJSON, farm)
    return farm, created
