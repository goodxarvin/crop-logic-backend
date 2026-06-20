from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import (
    Wallet,
    Transaction,
    TransactionType,
    DirectionType,
    StatusType,
)


class WalletService:

    @classmethod
    @transaction.atomic
    def create_topup_transaction(
        cls, wallet: Wallet, amount: Decimal, method: str
    ) -> Transaction:

        txn = Transaction.objects.create(
            wallet=wallet,
            transaction_type=TransactionType.TOPUP,
            direction_type=DirectionType.CREDIT,
            status_type=StatusType.PENDING,
            title="Wallet Topup",
            description=f"Topup of {amount} {wallet.currency.code} via {method}",
            amount=amount,
            method=method,
            balance_after=wallet.available_balance + amount,
        )

        return txn
