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
    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    )

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
    processing_status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    processing_error = models.TextField(blank=True, default="")
    task_id = models.CharField(max_length=255, blank=True, default="")
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



class CropProduct(models.Model):
    product_id = models.CharField(max_length=64, unique=True)
    label = models.CharField(max_length=255)
    color = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "crop_products"
        ordering = ["id"]

    def __str__(self):
        return self.label


class CropZoneRecommendation(models.Model):
    crop_zone = models.OneToOneField(
        CropZone,
        on_delete=models.CASCADE,
        related_name="recommendation",
    )
    product = models.ForeignKey(
        CropProduct,
        on_delete=models.PROTECT,
        related_name="zone_recommendations",
    )
    match_percent = models.PositiveIntegerField()
    water_need = models.CharField(max_length=128)
    estimated_profit = models.CharField(max_length=128)
    reason = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "crop_zone_recommendations"
        ordering = ["crop_zone_id"]

    def __str__(self):
        return f"{self.crop_zone.zone_id} -> {self.product.product_id}"


class CropZoneCriteria(models.Model):
    recommendation = models.ForeignKey(
        CropZoneRecommendation,
        on_delete=models.CASCADE,
        related_name="criteria",
    )
    name = models.CharField(max_length=128)
    value = models.PositiveIntegerField()
    sequence = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "crop_zone_criteria"
        ordering = ["sequence", "id"]

    def __str__(self):
        return f"{self.name}: {self.value}"


class CropZoneWaterNeedLayer(models.Model):
    LEVEL_LOW = "low"
    LEVEL_MEDIUM = "medium"
    LEVEL_HIGH = "high"
    LEVEL_CHOICES = (
        (LEVEL_LOW, "Low"),
        (LEVEL_MEDIUM, "Medium"),
        (LEVEL_HIGH, "High"),
    )

    crop_zone = models.OneToOneField(
        CropZone,
        on_delete=models.CASCADE,
        related_name="water_need_layer",
    )
    level = models.CharField(max_length=16, choices=LEVEL_CHOICES)
    value = models.CharField(max_length=128)
    color = models.CharField(max_length=32)

    class Meta:
        db_table = "crop_zone_water_need_layers"
        ordering = ["crop_zone_id"]


class CropZoneSoilQualityLayer(models.Model):
    LEVEL_LOW = "low"
    LEVEL_MEDIUM = "medium"
    LEVEL_HIGH = "high"
    LEVEL_CHOICES = (
        (LEVEL_LOW, "Low"),
        (LEVEL_MEDIUM, "Medium"),
        (LEVEL_HIGH, "High"),
    )

    crop_zone = models.OneToOneField(
        CropZone,
        on_delete=models.CASCADE,
        related_name="soil_quality_layer",
    )
    level = models.CharField(max_length=16, choices=LEVEL_CHOICES)
    score = models.PositiveIntegerField()
    color = models.CharField(max_length=32)

    class Meta:
        db_table = "crop_zone_soil_quality_layers"
        ordering = ["crop_zone_id"]


class CropZoneCultivationRiskLayer(models.Model):
    LEVEL_LOW = "low"
    LEVEL_MEDIUM = "medium"
    LEVEL_HIGH = "high"
    LEVEL_CHOICES = (
        (LEVEL_LOW, "Low"),
        (LEVEL_MEDIUM, "Medium"),
        (LEVEL_HIGH, "High"),
    )

    crop_zone = models.OneToOneField(
        CropZone,
        on_delete=models.CASCADE,
        related_name="cultivation_risk_layer",
    )
    level = models.CharField(max_length=16, choices=LEVEL_CHOICES)
    color = models.CharField(max_length=32)

    class Meta:
        db_table = "crop_zone_cultivation_risk_layers"
        ordering = ["crop_zone_id"]



class CropZoneAnalysis(models.Model):
    source = models.CharField(max_length=64, blank=True, default="")
    external_record_id = models.CharField(max_length=64, blank=True, default="")
    latitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    raw_response = models.JSONField(default=dict, blank=True)
    depths = models.JSONField(default=list, blank=True)
    crop_zone = models.OneToOneField(
        CropZone,
        on_delete=models.CASCADE,
        related_name="analysis",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "crop_zone_analyses"
        ordering = ["crop_zone_id"]


