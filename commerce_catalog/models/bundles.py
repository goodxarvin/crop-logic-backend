from django.db import models


class ProductBundle(models.Model):
    name = models.CharField(max_length=51)
    bundle_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}: {self.bundle_price}"


class ProductBundleItem(models.Model):
    bundle = models.ForeignKey("ProductBundle", on_delete=models.CASCADE, related_name="sku_item")
    sku = models.ForeignKey("commerce_catalog.SKU", on_delete=models.CASCADE, related_name="bundle_item")
    quantity = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["bundle", "sku"],
                name="unique_bundle_sku"
            )
        ]

    def __str__(self):
        return f"{self.bundle.name}: {self.sku.title}"