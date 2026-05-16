from django.db import models

class ProductVariant(models.Model):
    item = models.ForeignKey("commerce_catalog.SellableItem", on_delete=models.CASCADE, related_name="variant")
    name = models.CharField(max_length=30)
    is_active = models.BooleanField(default=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.item.title}: {self.name}"

class ProductAttributeValue(models.Model):
    variant = models.ForeignKey("ProductVariant", on_delete=models.CASCADE, related_name="attribute_value")
    value = models.CharField(max_length=60)
    display_order = models.PositiveIntegerField()
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    price_delta = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
        )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["variant"],
                condition=models.Q(is_default=True),
                name="only_one_attribute_can_be_the_main_selected",
            ),
            models.UniqueConstraint(
                fields=["variant", "value"],
                name="unique_value_per_variant"
            )
        ]