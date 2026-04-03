from django.core.management.base import BaseCommand

from sensor_catalog.models import SensorCatalog


SENSOR_CATALOG_ITEMS = [
    {
        "name": "Sensor 7 - Soil Moisture Sensor v1.2",
        "description": (
            "This sensor is typically the YL-69 or FC-28 soil moisture sensor. "
            "It measures only soil moisture and provides analog and digital outputs. "
            "It does not report soil temperature, pH, or nutrients."
        ),
        "customizable_fields": [],
        "supported_power_sources": ["solar", "direct_power"],
        "returned_data_fields": ["soil_moisture", "analog_output", "digital_output"],
        "sample_payload": {
            "soil_moisture": 42,
            "analog_output": 610,
            "digital_output": 1,
        },
        "is_active": True,
    }
]


class Command(BaseCommand):
    help = "Seed sensor catalog data."

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for item in SENSOR_CATALOG_ITEMS:
            sensor, created = SensorCatalog.objects.update_or_create(
                name=item["name"],
                defaults={
                    "description": item["description"],
                    "customizable_fields": item["customizable_fields"],
                    "supported_power_sources": item["supported_power_sources"],
                    "returned_data_fields": item["returned_data_fields"],
                    "sample_payload": item["sample_payload"],
                    "is_active": item["is_active"],
                },
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created sensor catalog item: {sensor.name}"))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f"Updated sensor catalog item: {sensor.name}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Sensor catalog seeding complete. Created: {created_count}, Updated: {updated_count}"
            )
        )
