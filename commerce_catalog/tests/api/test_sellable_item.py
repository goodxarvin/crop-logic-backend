import pytest
import logging
from django.urls import reverse
from commerce_catalog.tests.api.factories import (
    SellableItemFactory,
    SKUFactory,
    BasePriceFactory,
)

logger = logging.getLogger(__name__)


@pytest.mark.django_db
class TestSellableItemAPI:

    def test_get_list_sellable_item(self, auth_client):
        url = reverse("commerce-catalog:api-urls:get-sellable-items-list")
        BasePriceFactory.create_batch(3)

        response = auth_client.get(url)

        assert response.status_code == 200
        assert len(response.data["results"]) == 3

    def test_get_details_sellable_item(self, auth_client):

        price_instance = BasePriceFactory.create()
        sellable_item = price_instance.sku.item

        url = reverse(
            "commerce-catalog:api-urls:get-sellable-items-detail",
            kwargs={"uuid": str(sellable_item.uuid)},
        )
        response = auth_client.get(url)
        assert response.status_code == 200
        assert response.data["title"] == sellable_item.title
        assert response.data["uuid"] == str(sellable_item.uuid)


# @pytest.mark.django_db
# def test_get_list_sellable_item(self, auth_client):
#     BasePriceFactory.create_batch()

#     url = reverse("commerce-catalog:api-urls:get-sellable-items-list")
#     response = auth_client.get(url)

#     logging.info("\n📦 ALL ITEMS IN DB:", [item for item in response.data])

#     assert response.status_code == 200
