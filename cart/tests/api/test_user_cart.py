import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from commerce_catalog.tests.api.factories import BasePriceFactory
from .factories import CartItemFactory, FarmHubFactory

User = get_user_model()


@pytest.mark.django_db
class TestCartAPI:

    def test_get_list_cart(self, auth_client):
        url = reverse("cart:api-urls:cart-items-list")

        user = User.objects.get(username="test_wallet_features")

        CartItemFactory.create_batch(3, cart=user.cart, farm__owner=user)

        response = auth_client.get(url)

        assert response.status_code == 200
        assert "items" in list(response.data.keys())
        assert len(response.data["items"]) == 3
        assert int(response.data["total_price"])

    def test_post_create_cart_item(self, auth_client):
        url = reverse("cart:api-urls:cart-items-add-item")

        user = User.objects.get(username="test_wallet_features")

        sku = BasePriceFactory.create().sku
        farm = FarmHubFactory.create(owner=user)

        payload = {
            "sku": str(sku.id),
            "quantity": 1,
            "farm": str(farm.id),
        }

        response = auth_client.post(url, data=payload, format="json")

        assert response.status_code == 201
        assert "items" in list(response.data.keys())
        assert len(response.data["items"]) == 1
        assert int(response.data["total_price"])

    def test_post_add_one_quantity_cart_item(self, auth_client):
        url = reverse("cart:api-urls:cart-items-add-one-item-quantity")

        user = User.objects.get(username="test_wallet_features")

        cart_item = CartItemFactory.create(
            cart=user.cart,
            quantity=3,
            farm__owner=user,
        )
        sku_id = cart_item.sku.id
        farm_id = cart_item.farm.id

        payload = {
            "sku": str(sku_id),
            "farm": str(farm_id),
        }

        response = auth_client.post(url, data=payload, format="json")

        assert response.status_code == 200
        assert "items" in list(response.data.keys())
        assert len(response.data["items"]) == 1
        assert response.data["items"][0]["quantity"] == 4
        assert int(response.data["total_price"])

    def test_post_subtract_one_quantity_cart_item(self, auth_client):
        url = reverse("cart:api-urls:cart-items-subtract-one-item-quantity")

        user = User.objects.get(username="test_wallet_features")

        cart_item = CartItemFactory.create(
            cart=user.cart,
            quantity=3,
            farm__owner=user,
        )
        sku_id = cart_item.sku.id
        farm_id = cart_item.farm.id

        payload = {
            "sku": str(sku_id),
            "farm": str(farm_id),
        }

        response = auth_client.post(url, data=payload, format="json")

        assert response.status_code == 200
        assert "items" in list(response.data.keys())
        assert len(response.data["items"]) == 1
        assert response.data["items"][0]["quantity"] == 2
        assert int(response.data["total_price"])

    def test_post_delete_cart_item(self, auth_client):
        url = reverse("cart:api-urls:cart-items-remove-item")

        user = User.objects.get(username="test_wallet_features")

        cart_item = CartItemFactory.create(
            quantity=6,
            cart=user.cart,
            farm__owner=user,
        )
        sku_id = cart_item.sku.id
        farm_id = cart_item.farm.id

        payload = {
            "sku": str(sku_id),
            "farm": str(farm_id),
        }

        response = auth_client.post(url, data=payload, format="json")

        assert response.status_code == 200
        assert "items" in list(response.data.keys())
        assert len(response.data["items"]) == 0
        assert int(response.data["total_price"]) == 0
