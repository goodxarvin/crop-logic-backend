from django.db import models

import uuid
from django.db import models
from django.conf import settings


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

    checkout_session_uuid = models.UUIDField(
        null=True, blank=True, verbose_name="checkout_session_uuid"
    )

    total_amount = models.PositiveIntegerField(verbose_name="total_order_amount")

    status = models.CharField(
        max_length=20,
        choices=StatusType.choices,
        default=StatusType.PENDING,
        verbose_name="order_status",
    )

    shipping_address_snapshot = models.JSONField(
        null=True,
        blank=True,
    )
    farm_address_snapshot = models.JSONField(
        null=True,
        blank=True,
    )

    items_snapshot = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.uuid} - {self.user.username} ({self.get_status_display()})"
