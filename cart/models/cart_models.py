from django.db import models
from django.conf import settings
from uuid import uuid4
from decimal import Decimal
from pricing.services import PricingService


class Cart(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"cart of {self.user.username} - {self.uuid}"

    @property
    def total_items_count(self):
        return sum(item.quantity for item in self.cart_items.all())

    @property
    def total_items_base_price(self):
        return sum(item.total_sku_base_price for item in self.cart_items.all())

    @property
    def total_items_discount_price(self):
        return sum(item.total_sku_discount_amount for item in self.cart_items.all())

    @property
    def total_items_price(self):
        return sum(item.final_sku_price for item in self.cart_items.all())


class CartItem(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="cart_items")
    sku = models.ForeignKey(
        "commerce_catalog.SKU", on_delete=models.CASCADE, related_name="cart_items"
    )
    quantity = models.PositiveIntegerField(default=1)
    farm = models.ForeignKey(
        "farm_hub.FarmHub",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cart_items",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def pricing_details(self):
        try:
            sku_price_details = PricingService.calculate_final_sku_price(
                sku=self.sku,
                quantity=self.quantity,
                farm=self.farm,
            )
            print("---------------------------------------", sku_price_details)
            return sku_price_details

        except Exception as e:
            print("-------------------------", str(e))

    @property
    def total_sku_base_price(self):
        return self.pricing_details["total_base_price"]

    @property
    def total_sku_discount_amount(self):
        return self.pricing_details["total_discount_amount"]

    @property
    def final_sku_price(self):
        return self.pricing_details["total_final_price"]

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "sku", "farm"],
                name="unique_record_per_cart_sku_farm_fields",
            ),
        ]
