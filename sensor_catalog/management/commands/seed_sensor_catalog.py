from django.core.management.base import BaseCommand

from sensor_catalog.management import seed_sensor_catalog


class Command(BaseCommand):
    help = "Seed sensor catalog data."

    def handle(self, *args, **options):
        results, created_count, updated_count = seed_sensor_catalog()
        for sensor, created in results:
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created sensor catalog item: {sensor.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Updated sensor catalog item: {sensor.name}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Sensor catalog seeding complete. Created: {created_count}, Updated: {updated_count}"
            )
        )
