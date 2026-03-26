from django.core.management.base import BaseCommand, CommandError

from sensor_hub.seeds import seed_admin_sensor


class Command(BaseCommand):
    help = "Create or update the default full sensor for the admin user."

    def handle(self, *args, **options):
        try:
            sensor, created = seed_admin_sensor()
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        action = "created" if created else "updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"Admin sensor {action}: uuid_sensor={sensor.uuid_sensor}, "
                f"name={sensor.name}, owner={sensor.owner.username}"
            )
        )
