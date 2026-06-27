import logging
import requests
from django.conf import settings
from django.db import transaction
from config.failure_contract import StructuredServiceError
from config.observability import observe_operation
from order.models import Order
from .models import Payment, PaymentStatus

logger = logging.getLogger(__name__)

ZARINPAL_REQUEST_URL = "https://sandbox.zarinpal.com/pg/v4/payment/request.json"
ZARINPAL_START_PAY_URL = (
    "https://sandbox.zarinpal.com/pg/pages/Multi-Pool/Pay.html?Authority="
)


class PaymentService:

    @classmethod
    def initiate_payment(cls, user, checkout, amount) -> tuple:
        order = Order.objects.filter(
            user=user,
            checkout_uuid=checkout.uuid,
        ).first()

        payment = Payment.objects.create(
            user=user,
            amount=amount,
            order_uuid=order.uuid,
            status=PaymentStatus.PENDING,
        )

        payload = {
            "merchant_id": "00000000-0000-0000-0000-000000000000",
            "amount": int(amount) if int(amount) >= 1000 else 1000,
            "description": f"Topup of {amount} {user.wallet.currency.code} for user {user.email}",
            "callback_url": f"http://localhost:8000/api/payment/callback/",
            "metadata": {
                "mobile": user.phone_number,
                "email": user.email,
            },
        }

        with observe_operation(
            source="payment_service", provider="zarinpal", operation="request_token"
        ) as observer:
            try:
                response = requests.post(
                    ZARINPAL_REQUEST_URL,
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

        if errors or not data:
            payment.status = PaymentStatus.FAILED
            payment.save(update_fields=["status"])

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

        redirect_url = f"{ZARINPAL_START_PAY_URL}{authority}"
        return (redirect_url, authority, order, checkout)
