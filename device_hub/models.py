import uuid as uuid_lib

from django.db import models


class SensorCatalog(models.Model):
    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False, db_index=True)
    code = models.CharField(max_length=255, unique=True, db_index=True)
    name = models.CharField(max_length=255, unique=True, db_index=True)
    description = models.TextField(blank=True, default="")
    customizable_fields = models.JSONField(default=list, blank=True)
    supported_power_sources = models.JSONField(default=list, blank=True)
    returned_data_fields = models.JSONField(default=list, blank=True)
    sample_payload = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sensor_catalogs"
        ordering = ["code"]

    def __str__(self):
        return self.name


class FarmSensor(models.Model):
    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False, db_index=True)
    farm = models.ForeignKey("farm_hub.FarmHub", on_delete=models.CASCADE, related_name="sensors")
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


class SensorExternalRequestLog(models.Model):
    farm_uuid = models.UUIDField(db_index=True)
    sensor_catalog_uuid = models.UUIDField(null=True, blank=True, db_index=True)
    physical_device_uuid = models.UUIDField(db_index=True)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sensor_external_request_logs"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.physical_device_uuid}:{self.created_at.isoformat()}"

