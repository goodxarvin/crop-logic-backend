from django.db import models
from django.core.exceptions import ValidationError


class BasePrice(models.Model):
    sku = models.OneToOneField(
        "commerce_catalog.SKU", on_delete=models.CASCADE, related_name="base_prices"
    )
    amount = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    currency = models.ForeignKey(
        "pricing.Currency", on_delete=models.CASCADE, related_name="base_prices"
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()
        if self.amount <= 0:
            raise ValidationError("base price must be more than 0")

    def __str__(self):
        return f"{self.sku}: {self.amount} {self.currency.code}"


class PriceTier(models.Model):
    sku = models.ForeignKey(
        "commerce_catalog.SKU", on_delete=models.CASCADE, related_name="price_tier"
    )
    currency = models.ForeignKey(
        "pricing.Currency", on_delete=models.CASCADE, related_name="price_tier"
    )
    amount = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    min_quantity = models.PositiveIntegerField(default=1)
    max_quantity = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()
        if self.min_quantity > self.max_quantity:
            raise ValidationError("min_quantity must be less than max_quantity")
        if self.min_quantity <= 0:
            raise ValidationError("min_quantity must be more than 0")
        if self.amount <= 0:
            raise ValidationError("price tier amount must be more than 0")
        if self.max_quantity is not None:
            if self.min_quantity > self.max_quantity:
                raise ValidationError("min_quantity must be less than max_quantity")

    def __str__(self):
        max_q = self.max_quantity if self.max_quantity else "∞"
        return f"{self.sku} ({self.min_quantity}-{max_q}): {self.amount}"


class PriceType(models.TextChoices):
    BASE = "base", "base_price"
    TIER = "tier", "tier_price"


class PriceHistory(models.Model):
    price_type = models.CharField(
        max_length=10, choices=PriceType.choices, default=PriceType.BASE
    )
    sku = models.ForeignKey(
        "commerce_catalog.SKU", on_delete=models.CASCADE, related_name="price_history"
    )
    currency = models.ForeignKey(
        "pricing.Currency", on_delete=models.CASCADE, related_name="price_history"
    )
    old_price = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    new_price = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (
            f"{self.sku} | {self.old_price} -> {self.new_price} ({self.currency.code})"
        )
