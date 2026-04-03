from django.core.management.base import BaseCommand, CommandError

from account.seeds import ADMIN_USER_DATA
from farm_hub.seeds import seed_admin_farm


class Command(BaseCommand):
    help = "Create or update the default admin user through the admin farm seeder."

    def handle(self, *args, **options):
        try:
            farm, created = seed_admin_farm()
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        action = "created" if created else "updated"
        user = farm.owner
        self.stdout.write(
            self.style.SUCCESS(
                f"Admin user {action}: username={user.username}, email={user.email}, "
                f"phone_number={user.phone_number}, password={ADMIN_USER_DATA['password']}, "
                f"farm_uuid={farm.farm_uuid}"
            )
        )
