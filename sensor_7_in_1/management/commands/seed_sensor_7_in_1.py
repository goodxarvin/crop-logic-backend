from django.core.management.base import BaseCommand, CommandError

from sensor_7_in_1.seeds import seed_sensor_7_in_1_demo_data


class Command(BaseCommand):
    help = "Create or refresh demo sensor 7 in 1 data for summary and chart endpoints."

    def handle(self, *args, **options):
        try:
            result = seed_sensor_7_in_1_demo_data()
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(
                "Sensor 7 in 1 demo data seeded: "
                f"farm_uuid={result['farm'].farm_uuid}, "
                f"sensor_catalog={result['sensor_catalog'].code}, "
                f"physical_device_uuid={result['sensor'].physical_device_uuid}, "
                f"logs={result['log_count']}"
            )
        )
