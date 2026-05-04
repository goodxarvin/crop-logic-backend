import uuid

from django.db import models
from django.utils import timezone

from farm_hub.models import FarmHub


class IrrigationRecommendationRequest(models.Model):
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_PENDING_CONFIRMATION = "pending_confirmation"
    STATUS_COMPLETED = "completed"
    STATUS_ERROR = "error"
    STATUS_CHOICES = (
        (STATUS_IN_PROGRESS, "در حال اجرا"),
        (STATUS_PENDING_CONFIRMATION, "منتظر تایید"),
        (STATUS_COMPLETED, "پایان یافته"),
        (STATUS_ERROR, "خطا"),
    )

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    farm = models.ForeignKey(
        FarmHub,
        on_delete=models.CASCADE,
        related_name="irrigations",
    )
    crop_id = models.CharField(max_length=255, blank=True, default="")
    growth_stage = models.CharField(max_length=255, blank=True, default="")
    task_id = models.CharField(max_length=255, blank=True, default="", db_index=True)
    status = models.CharField(
        max_length=64,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING_CONFIRMATION,
        db_index=True,
    )
    request_payload = models.JSONField(default=dict, blank=True)
    response_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "irrigation_requests"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.task_id or str(self.uuid)


class IrrigationPlan(models.Model):
    SOURCE_RECOMMENDATION = "recommendation"
    SOURCE_FREE_TEXT = "free_text"
    SOURCE_CHOICES = (
        (SOURCE_RECOMMENDATION, "توصیه هوش مصنوعی"),
        (SOURCE_FREE_TEXT, "متن آزاد کاربر"),
    )

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    farm = models.ForeignKey(
        FarmHub,
        on_delete=models.CASCADE,
        related_name="irrigation_plans",
    )
    source = models.CharField(max_length=32, choices=SOURCE_CHOICES, db_index=True)
    recommendation = models.ForeignKey(
        IrrigationRecommendationRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="plans",
    )
    title = models.CharField(max_length=255, blank=True, default="")
    crop_id = models.CharField(max_length=255, blank=True, default="")
    growth_stage = models.CharField(max_length=255, blank=True, default="")
    plan_payload = models.JSONField(default=dict, blank=True)
    request_payload = models.JSONField(default=dict, blank=True)
    response_payload = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=False, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "irrigation_plans"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.title or self.crop_id or str(self.uuid)

    def soft_delete(self):
        self.is_deleted = True
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "is_active", "deleted_at", "updated_at"])
