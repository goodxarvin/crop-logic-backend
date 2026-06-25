from django.db import transaction
from django.core.exceptions import ValidationError
from wallet.models import Transaction
from .models import LedgerAccount, LedgerTransaction, LedgerLine


class LedgerService:

    @classmethod
    def record_topup_ledger(cls, wallet_transaction: Transaction):
        amount = wallet_transaction.amount
        wallet = wallet_transaction.wallet
        #  user = wallet.user

        user_ledger_code = f"v1:wallet:{getattr(wallet, 'uuid', wallet.uuid)}"

        with transaction.atomic():
            try:
                user_ledger_account = LedgerAccount.objects.get(code=user_ledger_code)
            except LedgerAccount.DoesNotExist:
                raise ValidationError("user ledger account does not exist")

            try:
                bank_ledger_account = LedgerAccount.objects.get(code="zarinpal_1001")
            except LedgerAccount.DoesNotExist:
                raise ValidationError("bank ledger account does not exist")

            ledger_txn = LedgerTransaction.objects.create(
                description="user topup operation ledger transaction",
                wallet_transaction=wallet_transaction,
            )

            user_ledger_line = LedgerLine.objects.create(
                ledger_transaction=ledger_txn,
                account=user_ledger_account,
                amount=-amount,
            )
            bank_ledger_line = LedgerLine.objects.create(
                ledger_transaction=ledger_txn,
                account=bank_ledger_account,
                amount=amount,
            )

            total_balance = user_ledger_line.amount + bank_ledger_line.amount
            if total_balance != 0:
                raise ValidationError(
                    "total balance is unequal to 0 there is a was problem during transaction"
                )

            return ledger_txn
