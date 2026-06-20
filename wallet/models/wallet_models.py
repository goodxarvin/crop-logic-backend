from django.db import models
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
import uuid


class WalletStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    SUSPENDED = "suspended", "Suspended"
    PENDING = "pending", "Pending"


class Wallet(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="wallets"
    )
    status = models.CharField(
        max_length=20, choices=WalletStatus.choices, default=WalletStatus.ACTIVE
    )
    currency = models.ForeignKey(
        "pricing.Currency", on_delete=models.PROTECT, related_name="wallets"
    )
    available_balance = models.DecimalField(
        max_digits=18, decimal_places=6, default=Decimal("0")
    )
    held_balance = models.DecimalField(
        max_digits=18, decimal_places=6, default=Decimal("0")
    )
    pending_settlements = models.DecimalField(
        max_digits=18, decimal_places=6, default=Decimal("0")
    )
    total_balance = models.DecimalField(
        max_digits=18, decimal_places=6, default=Decimal("0")
    )
    last_activity = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wallet {self.uuid} - User {self.user_id}"

    def save(self, *args, **kwargs):
        self.total_balance = (
            self.available_balance + self.held_balance + self.pending_settlements
        )
        super().save(*args, **kwargs)


class TransactionType(models.TextChoices):
    TOPUP = "topup", "Topup"
    ORDER_PAYMENT = "order_payment", "Order Payment"
    REFUND = "refund", "Refund"
    ADJUSTMENT = "adjustment", "Adjustment"
    SETTLEMENT = "settlement", "Settlement"
    WITHDRAWAL = "withdrawal", "Withdrawal"
    CASHBACK = "cashback", "Cashback"


class DirectionType(models.TextChoices):
    CREDIT = "credit", "Credit"
    DEBIT = "debit", "Debit"


class StatusType(models.TextChoices):
    PENDING = "pending", "Pending"
    CONFIRMED = "confirmed", "Confirmed"
    REJECTED = "rejected", "Rejected"
    REVERSED = "reversed", "Reversed"


class Transaction(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(
        Wallet, on_delete=models.PROTECT, related_name="transactions"
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
    )
    direction_type = models.CharField(
        max_length=20,
        choices=DirectionType.choices,
    )
    status_type = models.CharField(max_length=20, choices=StatusType.choices)
    amount = models.DecimalField(max_digits=18, decimal_places=6)

    reference_type = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="نوع موجودیت مثل Order, PaymentIntent",
    )
    reference_id = models.CharField(
        max_length=100, null=True, blank=True, help_text="شناسه موجودیت متصل"
    )
    method = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="مثلا درگاه زرین‌پال یا انتقال پایا",
    )
    balance_after = models.DecimalField(
        max_digits=18, decimal_places=6, null=True, blank=True
    )
    metadata = models.JSONField(default=dict, blank=True)

    title = models.CharField(max_length=50, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    reason_code = models.CharField(
        max_length=50, blank=True, null=True, help_text="کد دلیل برای اصلاحیه‌های دستی"
    )
    operator_note = models.TextField(blank=True, null=True, help_text="یادداشت ادمین")
    actor_id = models.IntegerField(
        blank=True, null=True, help_text="آی‌دی ادمینی که این تراکنش را ثبت کرده"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["reference_type", "reference_id"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return (
            f"TXN {self.uuid} - {self.get_transaction_type_display()} - {self.amount}"
        )
