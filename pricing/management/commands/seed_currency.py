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
            is_active=True,
            defaults={
                "code": "IRR",
                "symbol": "rial",
                "exchange_rate": 1.000000,
                "is_base": True,
                "is_active": True,
            },
        )

        self.stdout.write(self.style.SUCCESS("currency created successfully..."))
