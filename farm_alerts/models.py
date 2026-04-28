import uuid as uuid_lib

from django.db import models

from farm_hub.models import FarmHub


SEVERITY_CHOICES = [
    ("info", "Info"),
    ("warning", "Warning"),
    ("error", "Error"),
    ("success", "Success"),
]


class FarmAlert(models.Model):
    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False, db_index=True)
    farm = models.ForeignKey(FarmHub, on_delete=models.CASCADE, related_name="farm_alerts", null=True, blank=True)
    external_alert_id = models.CharField(max_length=255, blank=True, default="", db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    color = models.CharField(max_length=32, default="info", choices=SEVERITY_CHOICES)
    suggested_action = models.TextField(blank=True, default="")
    source_metric_type = models.CharField(max_length=255, blank=True, default="")
    occurred_at = models.DateTimeField(null=True, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    raw_alert = models.JSONField(default=dict, blank=True)
    avatar_icon = models.CharField(max_length=64, blank=True, default="")
    avatar_color = models.CharField(max_length=32, blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "farm_alerts"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.color})"


class AnomalyDetection(models.Model):
    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False, db_index=True)
    farm = models.ForeignKey(FarmHub, on_delete=models.CASCADE, related_name="anomalies", null=True, blank=True)
    sensor = models.CharField(max_length=255)
    value = models.CharField(max_length=64)
    expected = models.CharField(max_length=64)
    deviation = models.CharField(max_length=64)
    severity = models.CharField(max_length=32, default="warning", choices=SEVERITY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "farm_anomaly_detections"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.sensor}: {self.value}"


class Recommendation(models.Model):
    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False, db_index=True)
    farm = models.ForeignKey(FarmHub, on_delete=models.CASCADE, related_name="recommendations", null=True, blank=True)
    title = models.CharField(max_length=255)
    subtitle = models.TextField(blank=True, default="")
    avatar_icon = models.CharField(max_length=64, blank=True, default="")
    avatar_color = models.CharField(max_length=32, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "farm_recommendations"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
