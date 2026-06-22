from django.db.models.signals import post_save
from django.dispatch import receiver
from wallet.models import Wallet
from .models import AccountType, LedgerAccount


@receiver(post_save, sender=Wallet)
def create_liable_ledger_account(sender, instance, created, **kwargs):

    if created:

        wallet_identifier = getattr(instance, "uuid", instance.id)
        ledger_code = f"v1:wallet:{wallet_identifier}"

        user_eamil = instance.user.email if hasattr(instance, "user") else "unknown"
        LedgerAccount.objects.create(
            name=f"user wallet: {wallet_identifier}",
            account_type=AccountType.LIABILITY,
            code=ledger_code,
        )
