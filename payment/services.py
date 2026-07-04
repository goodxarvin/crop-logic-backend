import logging
import requests
from django.conf import settings
from django.db import transaction
from config.failure_contract import StructuredServiceError
from config.observability import observe_operation
from checkout.models import CheckoutSession
from checkout.models import StatusType as SessionStatusType
from ledger.services import LedgerService
from order.models import Order
from order.models import StatusType as OrderStatusType
from wallet.models import (
    Wallet,
    Transaction,
    TransactionType,
)
from wallet.models import StatusType as TXNStatusType
from .models import Payment, PaymentStatus

logger = logging.getLogger(__name__)

ZARINPAL_REQUEST_URL = "https://sandbox.zarinpal.com/pg/v4/payment/request.json"
ZARINPAL_START_PAY_URL = "https://sandbox.zarinpal.com/pg/StartPay/"


class PaymentService:

    @classmethod
    @transaction.atomic
    def initiate_payment_bank_portal(
        cls,
        user,
        order: Order,
        checkout_session: CheckoutSession,
        payment: Payment,
        txn: Transaction,
        amount,
    ) -> str:

        payload = {
            "merchant_id": "00000000-0000-0000-0000-000000000000",
            "amount": int(amount) if int(amount) >= 1000 else 1000,
            "description": f"Topup of {amount} {user.wallet.currency.code} for user {user.email}",
            "callback_url": f"http://localhost:8000/api/checkout/callback/?checkout_session_id={checkout_session.uuid}&payment_id={payment.uuid}&txn_id={txn.uuid}&order_id={order.uuid}",
            "metadata": {
                "mobile": user.phone_number,
                "email": user.email,
            },
        }

        with observe_operation(
            source="payment_service", provider="zarinpal", operation="request_token"
        ) as observer:
            try:
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }
                response = requests.post(
                    ZARINPAL_REQUEST_URL,
                    headers=headers,
                    json=payload,
                    timeout=10,
                )
                response_data = response.json()

                payment.raw_request_log = response_data
                payment.save(update_fields=["raw_request_log"])
            except requests.RequestException as exc:
                raise StructuredServiceError(
                    error_code="gateway_network_error",
                    message="error while conncting to the bank portal.",
                    source="payment_service",
                    retriable=True,
                    details={"exception": str(exc)},
                )

        errors = response_data.get("errors")
        data = response_data.get("data")

        if (
            errors
            or not data
            or not response_data["data"].get("code")
            in [
                100,
                101,
            ]
        ):
            payment.status = PaymentStatus.FAILED
            txn.status_type = TXNStatusType.REJECTED
            checkout_session.status = SessionStatusType.CANCELLED
            payment.save(update_fields=["status"])
            txn.save(update_fields=["status_type"])
            checkout_session.save(update_fields=["status"])

            raise StructuredServiceError(
                error_code="gateway_rejected_request",
                message="bank portal rejected the payment request.",
                source="payment_service",
                retriable=False,
                details={"exception": str(errors)},
            )

        authority = data.get("authority")
        payment.authority = authority
        payment.save(update_fields=["authority"])

        txn.authority = authority
        txn.method = "zarinpal portal"
        txn.save(update_fields=["authority", "method"])

        redirect_url = f"{ZARINPAL_START_PAY_URL}{authority}"
        return redirect_url

    @classmethod
    @transaction.atomic
    def wallet_payment(
        cls,
        wallet: Wallet,
        payment: Payment,
        checkout_session: CheckoutSession,
        txn: Transaction,
        order: Order,
    ):
        txn.method = "wallet payment"

        if not order.is_payable_with_wallet:
            payment.status = PaymentStatus.FAILED
            checkout_session.status = SessionStatusType.CANCELLED
            txn.status_type = TXNStatusType.REJECTED
            payment.save(update_fields=["status"])
            checkout_session.save(update_fields=["status"])
            txn.save(update_fields=["status_type", "method"])
            raise StructuredServiceError(
                error_code="wallet_insufficient_error",
                message="insufficient money in wallet",
                source="payment_service",
                retriable=False,
            )

        wallet.available_balance -= order.total_amount
        wallet.save(update_fields=["available_balance"])
        payment.status = PaymentStatus.SUCCESS
        checkout_session.status = SessionStatusType.COMPLETED
        txn.status_type = TXNStatusType.CONFIRMED
        order.status = OrderStatusType.PAID
        payment.save(update_fields=["status"])
        checkout_session.save(update_fields=["status"])
        txn.save(update_fields=["status_type", "method"])
        order.save(update_fields=["status"])

        order.cart.cart_items.all().delete()

        LedgerService.record_wallet_ledger(wallet_transaction=txn)

        return {"details": "successful wallet payment operation."}

    @classmethod
    @transaction.atomic
    def payment_verify_url(
        cls,
        checkout_session_uuid,
        payment_uuid,
        txn_uuid,
        order_uuid,
        authority,
    ) -> dict:
        try:
            checkout_session = CheckoutSession.objects.select_for_update().get(
                pk=checkout_session_uuid
            )
            txn = Transaction.objects.select_for_update().get(pk=txn_uuid)
            order = Order.objects.select_for_update().get(pk=order_uuid)
            payment = Payment.objects.select_for_update().get(pk=payment_uuid)
        except Exception as e:
            raise StructuredServiceError(
                error_code="record_not_found",
                message="One or more related payment records were not found.",
                source="payment_service",
                retriable=False,
            )

        verify_url = "https://sandbox.zarinpal.com/pg/v4/payment/verify.json"

        payload = {
            "merchant_id": "00000000-0000-0000-0000-000000000000",
            "amount": int(txn.amount) if int(txn.amount) >= 1000 else 1000,
            "authority": authority,
        }

        with observe_operation(
            source="payment_service", provider="zarinpal", operation="request_token"
        ) as observer:
            try:
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }
                response = requests.post(
                    verify_url, json=payload, headers=headers, timeout=10
                )
                response_data = response.json()

            except requests.RequestException as exc:
                raise StructuredServiceError(
                    error_code="gateway_verify_error",
                    message="error while conncting to the bank portal to verify payment.",
                    source="payment_service",
                    retriable=True,
                    details={"exception": str(exc)},
                )

        errors = response_data.get("errors")
        data = response_data.get("data")

        if (
            errors
            or not data
            or not response_data["data"].get("code")
            in [
                100,
                101,
            ]
        ):
            payment.status = PaymentStatus.FAILED
            checkout_session.status = SessionStatusType.CANCELLED
            txn.status_type = TXNStatusType.REJECTED
            payment.save(update_fields=["status"])
            checkout_session.save(update_fields=["status"])
            txn.save(update_fields=["status_type"])

            raise StructuredServiceError(
                error_code="gateway_rejected_request",
                message="bank portal rejected the payment request.",
                source="payment_service",
                retriable=False,
                details={"exception": str(errors)},
            )

        if txn.transaction_type != TransactionType.ORDER_PAYMENT:
            raise ValueError("Transaction must be a order_payment")

        if txn.status_type != TXNStatusType.PENDING:
            raise ValueError("Transaction must be pending")

        if checkout_session.status != SessionStatusType.AWAITING_PAYMENT:
            raise ValueError("CheckoutSession must be awaiting_payment")

        if payment.status != PaymentStatus.PENDING:
            raise ValueError("Payment is must be pending")

        if order.status != OrderStatusType.PENDING:
            raise ValueError("Order is must be pending")

        ref_id = response_data["data"]["ref_id"]

        txn.status_type = TXNStatusType.CONFIRMED
        txn.reference_type = "GatewayPayment"
        txn.reference_id = ref_id
        payment.status = PaymentStatus.SUCCESS
        checkout_session.status = SessionStatusType.COMPLETED
        order.status = OrderStatusType.PAID

        txn.save(update_fields=["status_type", "reference_type", "reference_id"])
        payment.save(update_fields=["status"])
        order.save(update_fields=["status"])

        LedgerService.record_topup_ledger(wallet_transaction=txn)

        order.cart.cart_items.all().delete()

        return {"details": "bank payment successful"}
