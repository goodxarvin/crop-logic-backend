from django.core.management.base import BaseCommand
from ...models import LedgerAccount, AccountType


class Command(BaseCommand):
    help = "initiate ledger account for zarinpal"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    #     self.faker = Faker()

    def handle(self, *args, **options):

        print("creating zarinpal and wallet pay ledger model instance...")

        LedgerAccount.objects.get_or_create(
            name="zarinpal ledger aacount",
            account_type=AccountType.ASSET,
            code="zarinpal_1001",
        )

        LedgerAccount.objects.get_or_create(
            name="direct wallet ledger aacount",
            account_type=AccountType.ASSET,
            code="direct_wallet_pay_1002",
        )

        self.stdout.write(
            self.style.SUCCESS("zarinpal and wallet pay ledger account cretaed.")
        )
