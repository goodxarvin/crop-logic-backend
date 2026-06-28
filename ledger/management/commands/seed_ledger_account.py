from django.core.management.base import BaseCommand
from ...models import LedgerAccount, AccountType


class Command(BaseCommand):
    help = "initiate ledger account for zarinpal"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    #     self.faker = Faker()

    def handle(self, *args, **options):

        print("creating zarinpal ledger model instance...")

        zarinpal_ledger_account = LedgerAccount.objects.create(
            name="zarinpal ledger aacount",
            account_type=AccountType.ASSET,
            code="zarinpal_1001",
        )

        self.stdout.write(self.style.SUCCESS("zarinpal ledger account cretaed."))
