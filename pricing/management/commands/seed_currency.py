from django.core.management.base import BaseCommand
from django.db.models import Q
from ...models import Currency


class Command(BaseCommand):
    help = "fake address creator"

    def handle(self, *args, **options):

        print("creating IRR currency...")

        Currency.objects.get_or_create(
            code="IRR",
            symbol="rial",
            is_base=True,
        )

        self.stdout.write(self.style.SUCCESS("currency created successfully..."))
