from django.db import models
from django.core.exceptions import ValidationError
import uuid


class AccountType(models.TextChoices):
    ASSET = "asset", "Asset"
    LIABILITY = "liability", "Liability"
    REVENUE = "revenue", "Revenue"
    EXPENSE = "expense", "Expense"


class LedgerAccount(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    account_type = models.CharField(max_length=20, choices=AccountType.choices)
    code = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.code}) - {self.account_type}"


class LedgerTransaction(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = models.TextField(blank=True, null=True)
    wallet_transaction = models.OneToOneField(
        "wallet.Transaction",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ledger_entry",
    )
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    def __str__(self):
        return f"{self.uuid} - {self.created_at.strftime('%Y-%m-%d %H: %M')}"


class LedgerLine(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ledger_transaction = models.ForeignKey(
        LedgerTransaction,
        on_delete=models.CASCADE,
        related_name="ledger_lines",
    )
    account = models.ForeignKey(
        LedgerAccount, on_delete=models.PROTECT, related_name="ledger_lines"
    )
    amount = models.DecimalField(max_digits=18, decimal_places=6)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
