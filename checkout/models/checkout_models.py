from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from uuid import uuid4
from address.models import AddressType


class StatusType(models.TextChoices):
    DRAFT = "draft", "Draft"
    AWAITING_REQUIREMENTS = "awaiting_requirements", "Awaiting_requirements"
    AWAITING_PAYMENT = "awaiting_payment", "Awaiting_payment"
    PAYMENT_PROCESSING = "payment_processing", "payment_processing"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"
    EXPIRED = "expired", "Expired"


class CheckoutSession(models.Model):

    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="checkout_sessions",
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
        max_length=30, choices=StatusType.choices, default=StatusType.DRAFT
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

    pricing_snapshot = models.JSONField(default=dict, blank=True)
    shipping_address_snapshot = models.JSONField(default=dict, blank=True)
    farm_address_snapshot = models.JSONField(default=dict, blank=True)
    billing_address_snapshot = models.JSONField(default=dict, blank=True)

    customer_notes = models.TextField(blank=True, null=True)

    payment_deadline_at = models.DateTimeField(null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Checkout {self.uuid} - {self.user.username} ({self.status})"

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
