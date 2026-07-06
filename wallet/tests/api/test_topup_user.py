import pytest
import responses
from django.contrib.auth import get_user_model
from django.urls import reverse
from .factories import TopupTransactionFactory, BankLedgerFactory

User = get_user_model()


@pytest.mark.django_db
class TestTopupAPI:

    @responses.activate
    def test_post_initiate_topup(self, auth_client):

        zarinpal_url = "https://sandbox.zarinpal.com/pg/v4/payment/request.json"

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
            url=zarinpal_url,
            json=mock_response,
            status=200,
        )

        url = reverse("wallet:api-urls:wallet-topup")

        payload = {"amount": 100_000.00}

        response = auth_client.post(url, data=payload, format="json")

        api_keys = list(response.data.keys())

        assert response.status_code == 201
        assert "message" in api_keys
        assert "payment_link" in api_keys
        assert "transaction_uuid" in api_keys
        assert "S00000000000000000000000000000n8jggj" in response.data["payment_link"]

    @responses.activate
    def test_post_verify_topup_callback(self, auth_client):

        zarinpal_verify_url = "https://sandbox.zarinpal.com/pg/v4/payment/verify.json"

        mock_verify_payload = {
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
            json=mock_verify_payload,
            status=200,
        )

        mock_auth_str = "S00000000000000000000000000000n8jggj"

        user = User.objects.get(username="test_wallet_features")

        BankLedgerFactory.create()

        topup_txn = TopupTransactionFactory.create(
            wallet=user.wallet,
            authority=mock_auth_str,
        )

        payload = {
            "txn_id": str(topup_txn.uuid),
            "Authority": mock_auth_str,
            "Status": "OK",
        }

        url = reverse("wallet:api-urls:wallet-callback")
        response = auth_client.get(url, data=payload)

        api_keys = list(response.data.keys())

        assert response.status_code == 200
        assert "message" in api_keys
        assert "ref_id" in api_keys

    def test_post_verify_topup_callback_404(self, auth_client):

        payload = {
            "txn_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",  # fake uuid
            "Authority": "S00000000000000000000000000000n8jggj",
            "Status": "OK",
        }

        url = reverse("wallet:api-urls:wallet-callback")
        response = auth_client.get(url, data=payload)

        api_keys = list(response.data.keys())

        assert response.status_code == 404
        assert "error" in api_keys
