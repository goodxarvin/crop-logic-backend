from django.db import models
from django.db import models
from django.core.exceptions import ValidationError
import uuid
from django.conf import settings
from address.models import Address, AddressType


class StatusType(models.TextChoices):
    PENDING = "pending", "Pending"
    PAID = "paid", "Paid"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"
    COMPLETED = "completed", "Completed"


class Order(models.Model):

    uuid = models.UUIDField(
        default=uuid.uuid4, unique=True, editable=False, primary_key=True
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name="user",
    )

    cart = models.ForeignKey(
        "cart.Cart", on_delete=models.PROTECT, related_name="checkout_sessions"
    )

    farm = models.ForeignKey(
        "farm_hub.FarmHub",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="checkout_sessions",
    )

    status = models.CharField(
        max_length=20,
        choices=StatusType.choices,
        default=StatusType.PENDING,
        verbose_name="order_status",
    )

    shipping_address = models.ForeignKey(
        "address.Address",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    farm_address = models.ForeignKey(
        "address.Address",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    billing_address = models.ForeignKey(
        "address.Address",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    pricing_snapshot = models.JSONField(
        default=dict,
        blank=True,
    )
    shipping_address_snapshot = models.JSONField(
        default=dict,
        blank=True,
    )
    farm_address_snapshot = models.JSONField(
        default=dict,
        blank=True,
    )
    billing_address_snapshot = models.JSONField(
        default=dict,
        blank=True,
    )

    items_snapshot = models.JSONField(
        null=True,
        blank=True,
    )

    customer_notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.uuid} - {self.user.username} ({self.status})"

    @property
    def get_requirements(self):

        cart_items = self.cart.cart_items.all()

        needs_shipping_address = any(
            getattr(item.sku.item, "requires_shipping_address", False)
            for item in cart_items
        )
        needs_farm_address = any(
            getattr(item.sku.item, "requires_farm_address", False)
            for item in cart_items
        )
        return {
            "requires_shipping_address": needs_shipping_address,
            "requires_farm_address": needs_farm_address,
        }

    def clean(self):
        super().clean()

        if (
            self.shipping_address
            and getattr(self.shipping_address, "address_type", None)
            != AddressType.SHIPPING
        ):
            raise ValidationError({"shipping_address": "incorrect address type."})

        if (
            self.farm_address
            and getattr(self.farm_address, "address_type", None)
            != AddressType.FARM_LOCATION
        ):
            raise ValidationError({"farm_address": "incorrect address type."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
