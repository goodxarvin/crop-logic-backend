import uuid

from django.db import transaction

from account.seeds import seed_admin_user
from sensor_catalog.models import SensorCatalog

from .catalog import CATALOG_SEED_DATA
from .models import FarmHub, FarmType, Product
from .services import dispatch_farm_zoning


ADMIN_FARM_UUID = uuid.UUID("11111111-1111-1111-1111-111111111111")
ADMIN_FARM_DATA = {
    "name": "Admin Smart Farm",
    "is_active": True,
    "sensors": [
        {
            "sensor_catalog_name": "Sensor 7 - Soil Moisture Sensor v1.2",
            "physical_device_uuid": uuid.UUID("22222222-2222-2222-2222-222222222221"),
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
        },
        {
            "sensor_catalog_name": "Sensor 7 - Soil Moisture Sensor v1.2",
            "physical_device_uuid": uuid.UUID("22222222-2222-2222-2222-222222222222"),
            "name": "Soil Probe 1",
            "sensor_type": "soil_probe",
            "is_active": True,
            "specifications": {
                "capabilities": ["soil_moisture", "soil_temperature", "ph", "ec"],
            },
            "power_source": {"type": "battery", "backup": "solar"},
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
    default_farm_type_name = "زراعی"
    created_products = []

    for farm_type_name, products in CATALOG_SEED_DATA.items():
        farm_type, _ = FarmType.objects.get_or_create(name=farm_type_name)
        for product_data in products:
            product, _ = Product.objects.update_or_create(
                farm_type=farm_type,
                name=product_data["name"],
                defaults={key: value for key, value in product_data.items() if key != "name"},
            )
            if farm_type_name == default_farm_type_name:
                created_products.append(product)

    return FarmType.objects.get(name=default_farm_type_name), created_products[:2]


def _get_sensor_catalog_by_name(name):
    return SensorCatalog.objects.filter(name=name).first()


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
        },
    )
    farm.products.set(products)
    farm.sensors.all().delete()
    sensors = []
    for sensor_data in ADMIN_FARM_DATA["sensors"]:
        sensor_data = sensor_data.copy()
        sensor_catalog_name = sensor_data.pop("sensor_catalog_name", None)
        sensor_data["sensor_catalog"] = _get_sensor_catalog_by_name(sensor_catalog_name) if sensor_catalog_name else None
        sensors.append(farm.sensors.model(farm=farm, **sensor_data))
    farm.sensors.bulk_create(sensors)
    if created:
        crop_area, _zoning_payload = dispatch_farm_zoning(ADMIN_FARM_AREA_GEOJSON, farm)
        farm.current_crop_area = crop_area
        farm.save(update_fields=["current_crop_area", "updated_at"])
    return farm, created
