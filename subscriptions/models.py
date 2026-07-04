from __future__ import annotations
from django.utils import timezone
import uuid as uuid_lib

from django.db import models


class SubscriptionPlan(models.Model):
    uuid = models.UUIDField(
        default=uuid_lib.uuid4, unique=True, editable=False, db_index=True
    )
    code = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    duration_days = models.PositiveIntegerField(
        default=30,
        null=True,
        blank=True,
        help_text="Duration of the subscription plan in days",
    )
    description = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "access_subscription_plans"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
