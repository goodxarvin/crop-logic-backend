import uuid as uuid_lib

from django.conf import settings
from django.db import models
from sensor_catalog.models import SensorCatalog


class FarmType(models.Model):
    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False, db_index=True)
    name = models.CharField(max_length=255, unique=True, db_index=True)
    description = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "farm_types"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False, db_index=True)
    farm_type = models.ForeignKey(
        FarmType,
        on_delete=models.CASCADE,
        related_name="products",
    )
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    light = models.CharField(max_length=255, blank=True, default="", help_text="نور مورد نیاز")
    watering = models.CharField(max_length=255, blank=True, default="", help_text="آبیاری")
    soil = models.CharField(max_length=255, blank=True, default="", help_text="خاک مناسب")
    temperature = models.CharField(max_length=255, blank=True, default="", help_text="دمای مناسب")
    planting_season = models.CharField(max_length=255, blank=True, default="", help_text="فصل کاشت")
    harvest_time = models.CharField(max_length=255, blank=True, default="", help_text="زمان برداشت")
    spacing = models.CharField(max_length=255, blank=True, default="", help_text="فاصله کاشت")
    fertilizer = models.CharField(max_length=255, blank=True, default="", help_text="کود مناسب")
    health_profile = models.JSONField(
        blank=True,
        default=dict,
        help_text=(
            "پروفایل سلامت محصول برای KPIها. ساختار نمونه: "
            '{"moisture": {"ideal_value": 65, "min_range": 45, "max_range": 75, "weight": 0.4}}'
        ),
    )
    irrigation_profile = models.JSONField(
        blank=True,
        default=dict,
        help_text=(
            "پروفایل آبیاری محصول برای محاسبات ETc. "
            '{"kc_initial": 0.6, "kc_mid": 1.15, "kc_end": 0.8, '
            '"growth_stage_duration": {"initial": 20, "mid": 30, "late": 25}}'
        ),
    )
    growth_profile = models.JSONField(
        blank=True,
        default=dict,
        help_text=(
            "پروفایل رشد محصول برای مدل GDD. "
            '{"base_temperature": 10, "required_gdd_for_maturity": 1200, '
            '"stage_thresholds": {"flowering": 500, "fruiting": 850}, "current_cumulative_gdd": 320}'
        ),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["farm_type", "name"], name="unique_product_per_farm_type"),
        ]

    def __str__(self):
        return self.name


class FarmHub(models.Model):
    farm_uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False, db_index=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="farm_hubs",
    )
    farm_type = models.ForeignKey(
        FarmType,
        on_delete=models.PROTECT,
        related_name="farms",
    )
    subscription_plan = models.ForeignKey(
        "access_control.SubscriptionPlan",
        on_delete=models.PROTECT,
        related_name="farms",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    current_crop_area = models.ForeignKey(
        "crop_zoning.CropArea",
        on_delete=models.SET_NULL,
        related_name="current_for_farms",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    products = models.ManyToManyField(Product, related_name="farms", blank=True)

    class Meta:
        db_table = "farm_hubs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.farm_uuid})"


class FarmSensor(models.Model):
    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False, db_index=True)
    farm = models.ForeignKey(
        FarmHub,
        on_delete=models.CASCADE,
        related_name="sensors",
    )
    sensor_catalog = models.ForeignKey(
        SensorCatalog,
        on_delete=models.PROTECT,
        related_name="farm_sensors",
        null=True,
        blank=True,
    )
    physical_device_uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    sensor_type = models.CharField(max_length=255, blank=True, default="")
    is_active = models.BooleanField(default=True)
    specifications = models.JSONField(default=dict, blank=True)
    power_source = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "farm_sensors"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.uuid})"
