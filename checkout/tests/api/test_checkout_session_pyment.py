import pytest
import responses
from django.urls import reverse
from django.core.management import call_command
from address.models import AddressType
from wallet.tests.api.factories import BankLedgerFactory, TransactionFactory
from wallet.models import TransactionType, DirectionType
from wallet.models import StatusType as TXNStatusType
from order.tests.api.factories import OrderFactory
from cart.tests.api.factories import CartItemFactory
from .factories import CheckoutSessionFactory, PaymentFactory
from ...models import StatusType as SessionStatusType


@pytest.fixture(scope="class")
def seed_province_city(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("seed_province_city")


@pytest.mark.django_db
@pytest.mark.usefixtures("seed_province_city")
class TestCheckoutSessionPaymentAPI:

    @responses.activate
    def test_post_initiate_payment_wallet_pay_false(self, auth_client, test_user):
        url = reverse("customer_notes:api-urls:checkout-initiate")
        zarinpal_request_url = "https://sandbox.zarinpal.com/pg/v4/payment/request.json"

        mock_response = {
            "data": {
                "authority": "S00000000000000000000000000000n8jggj",
                "fee": 3000,
                "fee_type": "Merchant",
                "code": 100,
                "message": "Success",
            },
            "errors": [],
        }

        responses.add(
            method=responses.POST,
            url=zarinpal_request_url,
            json=mock_response,
            status=200,
        )

        CartItemFactory.create_batch(
            3,
            cart=test_user.cart,
            farm__owner=test_user,
        )

        order = OrderFactory.create(
            user=test_user,
            cart=test_user.cart,
            farm__owner=test_user,
            shipping_address__address_type=AddressType.SHIPPING,
            shipping_address__user=test_user,
            farm_address__address_type=AddressType.FARM_LOCATION,
            farm_address__user=test_user,
            total_amount=test_user.cart.total_items_price,
            customer_notes="test note",
        )

        payload = {
            "order_uuid": str(order.uuid),
            "wallet_pay": False,
        }

        response = auth_client.post(url, data=payload, format="json")
        mock_redirect_url = "https://sandbox.zarinpal.com/pg/StartPay/S00000000000000000000000000000n8jggj"

        assert response.status_code == 200
        assert response.data["redirect_url"] == mock_redirect_url
        assert response.data["details"] == "payment portal_created_successfully"

    def test_post_initiate_payment_wallet_pay_true(self, auth_client, test_user):
        url = reverse("customer_notes:api-urls:checkout-initiate")

        wallet = test_user.wallet

        wallet.available_balance = 100_000_000
        wallet.save(update_fields=["available_balance"])

        CartItemFactory.create_batch(
            3,
            cart=test_user.cart,
            farm__owner=test_user,
        )

        order = OrderFactory.create(
            user=test_user,
            cart=test_user.cart,
            farm__owner=test_user,
            shipping_address__address_type=AddressType.SHIPPING,
            shipping_address__user=test_user,
            farm_address__address_type=AddressType.FARM_LOCATION,
            farm_address__user=test_user,
            total_amount=test_user.cart.total_items_price,
            customer_notes="test note",
        )

        BankLedgerFactory.create(
            name="direct wallet ledger account",
            code="direct_wallet_pay_1002",
        )

        payload = {
            "order_uuid": str(order.uuid),
            "wallet_pay": True,
        }

        response = auth_client.post(url, data=payload, format="json")

        assert response.status_code == 200
        assert response.data["details"] == "successful wallet payment operation."

    @responses.activate
    def test_get_callback_payment(self, auth_client, test_user):
        url = reverse("customer_notes:api-urls:checkout-callback")
        zarinpal_verify_url = "https://sandbox.zarinpal.com/pg/v4/payment/verify.json"

        mock_response = {
            "data": {
                "wages": None,
                "code": 100,
                "message": "Paid",
                "card_hash": "0866A6EAEA5CB085E4CF6EF19296BF19647552DD5F96F1E530DB3AE61837EFE7",
                "card_pan": "999999******9999",
                "ref_id": 199861901,
                "fee_type": "Merchant",
                "fee": 3000,
                "shaparak_fee": 1200,
                "order_id": None,
            },
            "errors": [],
        }

        responses.add(
            method=responses.POST,
            url=zarinpal_verify_url,
            json=mock_response,
            status=200,
        )

        mock_auth_str = "S00000000000000000000000000000n8jggj"

        CartItemFactory.create_batch(
            3,
            cart=test_user.cart,
            farm__owner=test_user,
        )

        items_list = []
        for item in test_user.cart.cart_items.all():
            items_list.append(
                {
                    "sku_id": item.sku.id,
                    "sku_title": item.sku.title,
                    "quantity": item.quantity,
                    "farm_id": item.farm.id if item.farm else None,
                    "base_price": item.total_sku_base_price,
                    "discount_amount": item.total_sku_discount_amount,
                    "final_price": item.final_sku_price,
                }
            )

        order = OrderFactory.create(
            user=test_user,
            cart=test_user.cart,
            farm__owner=test_user,
            shipping_address__address_type=AddressType.SHIPPING,
            shipping_address__user=test_user,
            farm_address__address_type=AddressType.FARM_LOCATION,
            farm_address__user=test_user,
            total_amount=test_user.cart.total_items_price,
            items_snapshot={"items": items_list},
            customer_notes="test note",
        )

        checkout_session = CheckoutSessionFactory.create(
            user=test_user,
            order_uuid=order.uuid,
            status=SessionStatusType.AWAITING_PAYMENT,
            total_amount=order.total_amount,
            shipping_address_snapshot=order.shipping_address_snapshot,
            farm_address_snapshot=order.farm_address_snapshot,
            items_snapshot=order.items_snapshot,
        )

        payment = PaymentFactory(
            user=test_user,
            amount=checkout_session.total_amount,
            order_uuid=order.uuid,
        )

        txn = TransactionFactory.create(
            wallet=test_user.wallet,
            transaction_type=TransactionType.ORDER_PAYMENT,
            direction_type=DirectionType.DEBIT,
            status_type=TXNStatusType.PENDING,
            amount=payment.amount,
        )

        BankLedgerFactory.create()

        payload = {
            "Status": "OK",
            "Authority": mock_auth_str,
            "checkout_session_id": str(checkout_session.uuid),
            "payment_id": str(payment.uuid),
            "txn_id": str(txn.uuid),
            "order_id": str(order.uuid),
        }

        response = auth_client.get(url, data=payload)

        assert response.status_code == 200
        assert response.data["details"] == "bank payment successful"
