import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def test_admin_user(db):
    admin_user, created = User.objects.get_or_create(
        username="test_wallet_features_admin",
        defaults={
            "email": "wallet@featurecrop.admin",
            "phone_number": "12129348",
        },
    )

    if created:
        admin_user.set_password("qazwsx123890")
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()

    return admin_user


@pytest.fixture
def auth_admin_client(test_admin_user):

    client = APIClient()

    client.force_authenticate(user=test_admin_user)

    refresh = RefreshToken.for_user(user=test_admin_user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    return client


@pytest.fixture
def test_user(db):

    user, created = User.objects.get_or_create(
        username="test_wallet_features",
        defaults={
            "email": "wallet@feature.crop",
            "phone_number": "123485890",
            "is_active": True,
        },
    )
    if created:
        user.set_password("qazwsx123890")
        user.save()
    return user


@pytest.fixture
def auth_client(test_user):

    client = APIClient()

    client.force_authenticate(user=test_user)

    refresh = RefreshToken.for_user(user=test_user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    return client
