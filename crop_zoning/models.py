import uuid

from django.db import models


class CropArea(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    geometry = models.JSONField(default=dict)
    points = models.JSONField(default=list)
    center = models.JSONField(default=dict)
    area_sqm = models.FloatField()
    area_hectares = models.FloatField()
    chunk_area_sqm = models.FloatField()
    zone_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "crop_areas"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"Area {self.uuid}"


class CropZone(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    crop_area = models.ForeignKey(
        CropArea,
        on_delete=models.CASCADE,
        related_name="zones",
    )
    zone_id = models.CharField(max_length=64)
    geometry = models.JSONField(default=dict)
    points = models.JSONField(default=list)
    center = models.JSONField(default=dict)
    area_sqm = models.FloatField()
    area_hectares = models.FloatField()
    sequence = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "crop_zones"
        ordering = ["sequence", "id"]
        constraints = [
            models.UniqueConstraint(fields=["crop_area", "zone_id"], name="unique_crop_area_zone_id"),
        ]

    def __str__(self):
        return self.zone_id
