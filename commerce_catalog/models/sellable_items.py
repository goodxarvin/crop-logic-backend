from django.db import models
from django.utils.text import slugify


class ItemType(models.TextChoices):
    SUBSCRIPTION_PALN = "subscription_plan", "Subscription Plan"
    PHYSICAL_DEVICE = "physical_device", "Physical Device"
    PHYSICAL_SUPPLY = "physical_supply", "Physical Supply"
    SERVICE = "service", "Service"
    INSTALLATION_SERVICE = "installation_service", "Installation Service"
    FARM_ANALYSIS = "farm_analysis", "Farm Analysis"
    CREDIT_TOPUP = "credit_topup", "Credit Topup"


class SellableItem(models.Model):
    item_type = models.CharField(
        max_length=32, choices=ItemType.choices, default=ItemType.PHYSICAL_SUPPLY
    )
    title = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, allow_unicode=True)
    description = models.TextField(blank=True)
    short_description = models.CharField(max_length=150, null=True, blank=True)
    image = models.ImageField(null=True, default=True)
    is_active = models.BooleanField(default=True)
    is_installable = models.BooleanField(default=False)
    requires_shipping_address = models.BooleanField(default=False)
    requires_farm_address = models.BooleanField(default=False)
    tax_class = models.ForeignKey(
        "commerce_catalog.TaxClass",
        on_delete=models.PROTECT,
        related_name="sellable_item",
    )
    external_source = models.CharField(max_length=50, null=True, blank=True)
    external_id = models.CharField(max_length=100, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["external_source", "external_id"],
                name="unique_external_product",
            )
        ]

    def __str__(self):
        return f"{self.title}: {self.is_active}"

    def save(
        self,
        *args,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        if not self.slug:
            self.slug = slugify(self.title)
        return super().save(
            *args,
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )
