import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_admin_client(db):

    client = APIClient()

    user = User.objects.create_user(
        username="test_wallet_features_admin",
        email="wallet@featurecrop.admin",
        phone_number="12129348",
        password="qazwsx123890",
    )

    user.is_staff = True
    user.is_superuser = True
    user.save()

    client.force_authenticate(user=user)

    refresh = RefreshToken.for_user(user=user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    return client


@pytest.fixture
def auth_client(db):

    client = APIClient()

    user = User.objects.create_user(
        username="test_wallet_features",
        email="wallet@feature.crop",
        phone_number="123485890",
        password="qazwsx123890",
    )

    client.force_authenticate(user=user)

    refresh = RefreshToken.for_user(user=user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    return client
