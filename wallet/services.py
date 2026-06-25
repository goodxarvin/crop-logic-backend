from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from ledger.services import LedgerService
from .models import (
    Wallet,
    Transaction,
    TransactionType,
    WithdrawalStatus,
    WithdrawalRequest,
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

        LedgerService.record_topup_ledger(wallet_transaction=txn)

        return txn

    @classmethod
    @transaction.atomic
    def create_withdrawal_request(
        cls,
        wallet: Wallet,
        amount: Decimal,
        shiba_number: str,
        account_holder_name: str,
        card_number: str = None,
    ):
        if amount <= 0:
            raise ValidationError("amount must be more than 0")

        wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)

        if wallet.available_balance < amount + 100_000:
            raise ValidationError(
                "least amount that should be in the wallet is 100,000 IRR, not enough balance"
            )

        wallet.available_balance -= amount
        wallet.held_balance += amount
        wallet.save()

        withdrawal_request_obj = WithdrawalRequest.objects.create(
            wallet=wallet,
            amount=amount,
            shiba_number=shiba_number,
            card_number=card_number,
            account_holder_name=account_holder_name,
            status=WithdrawalStatus.PENDING,
        )

        return withdrawal_request_obj

    @classmethod
    @transaction.atomic
    def approve_withdrawal_request(
        cls, request_uuid: str, bank_tracking_code: str = None
    ):

        req = WithdrawalRequest.objects.select_for_update().get(pk=request_uuid)

        if req.status != WithdrawalStatus.PENDING:
            raise ValidationError("this withdrawal has been processed")

        wallet = Wallet.objects.select_for_update().get(pk=req.wallet.pk)
        wallet.held_balance -= req.amount
        wallet.save()

        txn = Transaction.objects.create(
            wallet=wallet,
            amount=-req.amount,
            transaction_type=TransactionType.WITHDRAWAL,
            status_type=StatusType.CONFIRMED,
            description="withdrawal for user number",
            metadata={"bank_tracking_code": bank_tracking_code},
        )

        req.status = WithdrawalStatus.APPROVED
        req.bank_tracking_code = bank_tracking_code
        req.transaction = txn
        req.save()

        return req

    @classmethod
    @transaction.atomic
    def reject_withdrawal_request(cls, request_uuid: str, rejection_reason: str):

        req = WithdrawalRequest.objects.select_for_update().get(pk=request_uuid)

        if req.status != WithdrawalStatus.PENDING:
            raise ValidationError("this withdrawal has been processed")

        wallet = Wallet.objects.select_for_update().get(pk=req.wallet.pk)

        wallet.held_balance -= req.amount
        wallet.available_balance += req.amount
        wallet.save()

        req.status = WithdrawalStatus.REJECTED
        req.rejection_reason = rejection_reason
        req.save()

        return req
