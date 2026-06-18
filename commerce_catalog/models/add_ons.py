from django.db import models

class ProductAddOn(models.Model):
    name = models.CharField(max_length=51)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_multiple = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True) 
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class AddOnAssignment(models.Model):
    add_on = models.ForeignKey(
        "ProductAddOn",
        on_delete=models.CASCADE,
        related_name="addon_assignments")
    sellable_item = models.ForeignKey(
        "commerce_catalog.SellableItem",
        on_delete=models.CASCADE,
        related_name="addon_assignments")
    is_required = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["sellable_item", "add_on"],
                name="unique_addon_per_item"
            )
        ]

    def __str__(self):
        return f"{self.sellable_item.title}: {self.add_on.name}"