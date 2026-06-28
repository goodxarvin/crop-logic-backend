from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from uuid import uuid4
from address.models import AddressType


class StatusType(models.TextChoices):
    DRAFT = "draft", "Draft"
    AWAITING_PAYMENT = "awaiting_payment", "Awaiting_payment"
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

    order_uuid = models.UUIDField(db_index=True)

    status = models.CharField(
        max_length=30, choices=StatusType.choices, default=StatusType.DRAFT
    )

    total_amount = models.PositiveIntegerField(verbose_name="total_order_amount")
    shipping_address_snapshot = models.JSONField(default=dict, blank=True)
    farm_address_snapshot = models.JSONField(default=dict, blank=True)
    items_snapshot = models.JSONField(null=True, blank=True)

    payment_deadline_at = models.DateTimeField(null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Checkout {self.uuid} - {self.user.username} ({self.status})"
