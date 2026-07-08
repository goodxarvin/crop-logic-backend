import pytest
import decimal
from django.urls import reverse
from django.contrib.auth import get_user_model
from .factories import WithdrawalRequestFactory

User = get_user_model()


@pytest.mark.django_db
class TestWithdrawalAPI:

    def test_get_list_withdrawal_request(self, auth_client):

        user = User.objects.get(username="test_wallet_features")

        wallet = user.wallet
        wallet.available_balance += decimal.Decimal("10000000")
        wallet.save(update_fields=["available_balance"])

        url = reverse("wallet:api-urls:user-withdrawal-request")

        WithdrawalRequestFactory.create_batch(
            3,
            wallet=wallet,
            account_holder_name=str(user.username),
        )

        response = auth_client.get(url)

        results = response.data.get("results", None)

        assert response.status_code == 200
        assert len(results) == 3
        assert "amount" in results[0].keys()

    def test_post_create_withdrawal_request(self, auth_client):

        user = User.objects.get(username="test_wallet_features")

        wallet = user.wallet
        wallet.available_balance += decimal.Decimal("10000000")
        wallet.save(update_fields=["available_balance"])

        payload = {
            "amount": decimal.Decimal("90000"),
            "shiba_number": "IR_test_shiba_number000000",
            "card_number": "",
            "account_holder_name": str(user.username),
        }

        url = reverse("wallet:api-urls:user-withdrawal-request")

        response = auth_client.post(url, data=payload, format="json")

        results = response.data

        assert response.status_code == 201
        assert "amount" in results.keys()
        assert "90000.000000" in results.values()
