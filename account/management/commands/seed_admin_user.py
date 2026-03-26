from django.core.management.base import BaseCommand, CommandError

from account.seeds import ADMIN_USER_DATA, seed_admin_user


class Command(BaseCommand):
    help = "Create or update the default admin user."

    def handle(self, *args, **options):
        try:
            user, created = seed_admin_user()
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        action = "created" if created else "updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"Admin user {action}: username={user.username}, email={user.email}, "
                f"phone_number={user.phone_number}, password={ADMIN_USER_DATA['password']}"
            )
        )
