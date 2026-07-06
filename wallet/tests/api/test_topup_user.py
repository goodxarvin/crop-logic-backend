import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestTopupAPI:

    def test_post_initiate_topup(self, auth_client):
        url = reverse("wallet:api-urls:wallet-topup")

        payload = {"amount": 100_000.00}

        response = auth_client.post(url, data=payload, format="json")

        api_keys = list(response.data.keys())

        assert response.status_code == 201
        assert "message" in api_keys
        assert "payment_link" in api_keys
        assert "transaction_uuid" in api_keys
