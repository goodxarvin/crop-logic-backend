import uuid

from django.db import models

from farm_hub.models import FarmHub


class FertilizationRecommendationRequest(models.Model):
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_PENDING_CONFIRMATION = "pending_confirmation"
    STATUS_COMPLETED = "completed"
    STATUS_CHOICES = (
        (STATUS_IN_PROGRESS, "در حال مصرف"),
        (STATUS_PENDING_CONFIRMATION, "منتظر تایید"),
        (STATUS_COMPLETED, "پایان یافته"),
    )

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    farm = models.ForeignKey(
        FarmHub,
        on_delete=models.CASCADE,
        related_name="fertilization_recommendations",
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
        db_table = "fertilization_recommendation_requests"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.task_id or str(self.uuid)
