import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from .factories import TransactionFactory

User = get_user_model()


@pytest.mark.django_db
class TestUserWalletAccessAPI:

    def test_get_retrieve_user_wallet(self, auth_client):
        url = reverse("wallet:api-urls:my-wallet")

        response = auth_client.get(url)

        assert response.status_code == 200
        assert "available_balance" in list(response.data.keys())

    def test_get_list_user_transaction(self, auth_client):
        url = reverse("wallet:api-urls:my-transactions-list")

        user = User.objects.get(username="test_wallet_features")

        TransactionFactory.create_batch(size=3, wallet=user.wallet)

        response = auth_client.get(url)
        assert response.status_code == 200
        assert len(response.data["results"]) == 3
        assert "amount" in list(response.data["results"][1].keys())
        