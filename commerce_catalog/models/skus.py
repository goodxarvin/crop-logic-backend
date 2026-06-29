from django.db import models


class SKU(models.Model):
    item = models.ForeignKey(
        "commerce_catalog.SellableItem", on_delete=models.CASCADE, related_name="sku"
    )
    code = models.CharField(max_length=150, unique=True)
    title = models.CharField(max_length=51, blank=True)
    barcode = models.CharField(max_length=50, unique=True, null=True, blank=True)
    base_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    image = models.ImageField(null=True, default=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    attributes = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["item"],
                condition=models.Q(is_default=True),
                name="unique_default_sku_per_item",
            )
        ]

    def __str__(self):
        return f"{self.code}: {self.title}"
