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

    @classmethod
    @transaction.atomic
    def verify_confirm_topup(
        cls, transaction_uuid: str, gateway_ref_id: str
    ) -> Transaction:
        txn = Transaction.objects.select_for_update().get(
            uuid=transaction_uuid,
        )

        if txn.transaction_type != TransactionType.TOPUP:
            raise ValueError("Transaction must be a topup")

        if txn.status_type != StatusType.PENDING:
            raise ValueError("Transaction must be pending")

        if txn.status_type == StatusType.CONFIRMED:
            raise ValueError("Transaction is already confirmed")

        wallet = Wallet.objects.select_for_update().get(uuid=txn.wallet.uuid)
        wallet.available_balance += txn.amount
        wallet.last_activity = timezone.now()
        wallet.save()

        txn.status_type = StatusType.CONFIRMED
        txn.reference_type = "GatewayPayment"
        txn.reference_id = gateway_ref_id
        txn.balance_after = wallet.available_balance
        txn.save()

        return txn
