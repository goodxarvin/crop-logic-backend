import pytest
from address.models import AddressType
from django.urls import reverse
from django.core.management import call_command
from address.models import AddressType
from cart.tests.api.factories import CartItemFactory
from .factories import OrderFactory, AddressFactory, FarmHubFactory


@pytest.fixture(scope="class")
def seed_province_city(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("seed_province_city")


@pytest.mark.django_db
@pytest.mark.usefixtures("seed_province_city")
class TestOrderAPI:

    def test_get_list_order(self, auth_client, test_user):
        url = reverse("order:api-urls:orders-list")

        CartItemFactory.create_batch(
            3,
            cart=test_user.cart,
            farm__owner=test_user,
        )

        OrderFactory.create(
            user=test_user,
            cart=test_user.cart,
            farm__owner=test_user,
            shipping_address__address_type=AddressType.SHIPPING,
            shipping_address__user=test_user,
            farm_address__address_type=AddressType.FARM_LOCATION,
            farm_address__user=test_user,
            total_amount=test_user.cart.total_items_price,
        )

        response = auth_client.get(url)

        assert response.status_code == 200
        assert response.data["results"][0].get("uuid")
        assert len(response.data["results"]) == 1
        assert float(response.data["results"][0].get("total_amount")) > 0

    def test_post_create_order(self, auth_client, test_user):
        url = reverse("order:api-urls:orders-list")

        cart_items = CartItemFactory.create_batch(
            3,
            cart=test_user.cart,
            farm__owner=test_user,
        )

        shipping_address = AddressFactory.create(
            address_type=AddressType.SHIPPING,
            user=test_user,
        )

        farm_address = AddressFactory.create(
            address_type=AddressType.FARM_LOCATION,
            user=test_user,
        )

        payload = {
            "farm": str(cart_items[0].farm.pk),
            "shipping_address": str(shipping_address.pk),
            "farm_address": str(farm_address.pk),
            "billing_address": None,
            "customer_notes": "test note",
        }

        response = auth_client.post(url, data=payload, format="json")

        assert response.status_code == 201
        assert response.data["farm"] is not None
        assert response.data["shipping_address"] is not None
        assert response.data["farm_address"] is not None
        assert response.data["customer_notes"] is not None

    def test_post_finilize_order(self, auth_client, test_user):

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

        url = reverse("order:api-urls:orders-finilize", kwargs={"uuid": order.uuid})

        # payload = {
        #     "farm": None,
        #     "shipping_address": None,
        #     "farm_address": None,
        #     "billing_address": None,
        #     "customer_notes": "test finilize note",
        # }

        response = auth_client.post(url)

        assert response.status_code == 200
        assert response.data["farm"] is not None
        assert response.data["shipping_address"] is not None
        assert response.data["farm_address"] is not None
        assert response.data["customer_notes"] is not None
        assert str(response.data["uuid"]) == str(order.uuid)
        assert float(response.data.get("total_amount")) > 0
