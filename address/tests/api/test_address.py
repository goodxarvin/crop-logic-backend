import pytest
from django.urls import reverse
from django.core.management import call_command
from .factories import AddressFactory
from ...models import AddressType


@pytest.fixture(scope="class")
def seed_province_city(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("seed_province_city")


@pytest.mark.django_db
@pytest.mark.usefixtures("seed_province_city")
class TestAddressTestAPI:

    def test_get_list_provinces(self, auth_client):
        url = reverse("address:api-urls:get-provinces")

        response = auth_client.get(url)

        assert response.status_code == 200
        assert len(response.data) == 31
        assert response.data[30]["province_name"] == "البرز"

    def test_get_list_cities(self, auth_client):
        url = reverse("address:api-urls:get-cities", kwargs={"province_pk": 6})

        response = auth_client.get(url)

        assert response.status_code == 200
        assert len(response.data) > 0
        assert "city_name" in response.data[0].keys()

    def test_get_list_address(self, auth_client, test_user):
        url = reverse("address:api-urls:address-viewset-list")

        AddressFactory.create_batch(
            3,
            user=test_user,
        )

        response = auth_client.get(url)

        assert response.status_code == 200
        assert len(response.data) > 0
        assert "address_type" in response.data[0].keys()

    def test_post_create_address(self, auth_client):
        url = reverse("address:api-urls:address-viewset-list")

        payload = {
            "address_type": "shipping",
            "receiver_name": "test_name",
            "latitute": None,
            "longtitute": None,
            "receiver_phone": "test_912",
            "province": 1,
            "city": 1,
            "postal_code": "test_code",
            "address_detail": "test_detail",
        }

        response = auth_client.post(url, data=payload, format="json")

        assert response.status_code == 201
        assert "address_type" in response.data.keys()
        assert response.data["address_type"] in AddressType.values

    def test_get_retrieve_address(self, auth_client, test_user):

        address = AddressFactory.create(
            user=test_user,
        )

        url = reverse(
            "address:api-urls:address-viewset-detail", kwargs={"pk": address.pk}
        )

        response = auth_client.get(url)

        assert response.status_code == 200
        assert "address_type" in response.data.keys()
        assert response.data["address_type"] in AddressType.values

    def test_put_update_address(self, auth_client, test_user):

        address = AddressFactory.create(
            user=test_user,
        )
        url = reverse(
            "address:api-urls:address-viewset-detail", kwargs={"pk": address.pk}
        )

        payload = {
            "address_type": "shipping",
            "receiver_name": "test_edit",
            "latitute": 1.000,
            "longtitute": 1.000,
            "receiver_phone": "edit_912",
            "province": 2,
            "city": 2,
            "postal_code": "edit_code",
            "address_detail": "edit_detail",
        }

        response = auth_client.put(url, data=payload, format="json")

        assert response.status_code == 200
        assert "address_type" in response.data.keys()
        assert response.data["address_type"] in AddressType.values

    def test_delete_destroy_address(self, auth_client, test_user):

        address = AddressFactory.create(
            user=test_user,
        )

        url = reverse(
            "address:api-urls:address-viewset-detail", kwargs={"pk": address.pk}
        )

        response = auth_client.delete(url)

        assert response.status_code == 204
