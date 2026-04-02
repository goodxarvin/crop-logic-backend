import uuid

from django.conf import settings
from django.db import models


class FarmType(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
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
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    farm_type = models.ForeignKey(
        FarmType,
        on_delete=models.CASCADE,
        related_name="products",
    )
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
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
    farm_uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
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
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    customization = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    products = models.ManyToManyField(Product, related_name="farms", blank=True)

    class Meta:
        db_table = "farm_hubs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.farm_uuid})"


class FarmSensor(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    farm = models.ForeignKey(
        FarmHub,
        on_delete=models.CASCADE,
        related_name="sensors",
    )
    name = models.CharField(max_length=255)
    sensor_type = models.CharField(max_length=255, blank=True, default="")
    is_active = models.BooleanField(default=True)
    specifications = models.JSONField(default=dict, blank=True)
    power_source = models.JSONField(default=dict, blank=True)
    customization = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "farm_sensors"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.uuid})"
