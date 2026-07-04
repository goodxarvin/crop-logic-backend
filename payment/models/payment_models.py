from django.db import models
from django.conf import settings
from uuid import uuid4


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SUCCESS = "success", "Success"
    FAILED = "failed", "Failed"
    ALREADY_VERIFIED = "already_verified", "Already_verified"


class Payment(models.Model):

    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments"
    )

    order_uuid = models.UUIDField(db_index=True)
    checkout_session_uuid = models.UUIDField(db_index=True, null=True)

    amount = models.DecimalField(max_digits=12, decimal_places=0)

    authority = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
    )
    ref_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING
    )

    raw_request_log = models.JSONField(default=dict, blank=True)
    raw_callback_log = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment {self.uuid} - Order: {self.order_uuid} - {self.status}"
