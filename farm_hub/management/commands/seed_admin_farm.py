from django.core.management.base import BaseCommand, CommandError

from farm_hub.seeds import seed_admin_farm


class Command(BaseCommand):
    help = "Create or update the default farm hub for the admin user."

    def handle(self, *args, **options):
        try:
            farm, created = seed_admin_farm()
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        action = "created" if created else "updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"Admin farm {action}: farm_uuid={farm.farm_uuid}, name={farm.name}, owner={farm.owner.username}"
            )
        )
