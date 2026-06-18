from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.db import models


class DiscountType(models.TextChoices):
    FIXED = "fixed", "fixed_price"
    PERCENTAGE = "percentage", "percentage"


class DiscountPrice(models.Model):
    discount_type = models.CharField(
        max_length=15,
        choices=DiscountType.choices,
        default=DiscountType.FIXED,
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    percentage = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    usage_limit = models.PositiveIntegerField(default=0)
    used_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()
        if self.discount_type == DiscountType.FIXED and self.amount <= 0:
            raise ValidationError("price amount must be more than 0")
        if self.discount_type == DiscountType.PERCENTAGE and self.percentage <= 0:
            raise ValidationError("price percentage must be more than 0")
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError("end_date can not be erlier then the start_date")

    def __str__(self):
        if self.discount_type == DiscountType.PERCENTAGE:
            return f"{self.percentage}% Discount"
        return f"{self.amount} Fixed Discount"


class DiscountSKURelation(models.Model):
    sku = models.ForeignKey(
        "commerce_catalog.SKU",
        on_delete=models.CASCADE,
        related_name="discount_relation",
    )
    discount = models.ForeignKey(
        "pricing.DiscountPrice", on_delete=models.CASCADE, related_name="sku_relation"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["discount", "sku"], name="unique_discount_sku"
            )
        ]

    def __str__(self):
        return f"{self.sku.title}: {self.discount.amount}"


class DiscountSellableItemRelation(models.Model):
    sellable_item = models.ForeignKey(
        "commerce_catalog.SellableItem",
        on_delete=models.CASCADE,
        related_name="discount_relation",
    )
    discount = models.ForeignKey(
        "pricing.DiscountPrice",
        on_delete=models.CASCADE,
        related_name="sellable_item_relation",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["discount", "sellable_item"],
                name="unique_discount_sellable_item",
            )
        ]

    def __str__(self):
        return f"{self.sellable_item.title}: {self.discount.amount}"
