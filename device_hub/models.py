import uuid as uuid_lib

from django.db import models


class DeviceCatalog(models.Model):
    OUTPUT_ONLY = "output_only"
    INPUT_ONLY = "input_only"
    DEVICE_COMMUNICATION_TYPES = [
        (OUTPUT_ONLY, "Output Only"),
        (INPUT_ONLY, "Input Only"),
    ]

    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False, db_index=True)
    code = models.CharField(max_length=255, unique=True, db_index=True)
    name = models.CharField(max_length=255, unique=True, db_index=True)
    description = models.TextField(blank=True, default="")
    device_communication_type = models.CharField(
        max_length=32,
        choices=DEVICE_COMMUNICATION_TYPES,
        default=OUTPUT_ONLY,
        db_index=True,
    )
    customizable_fields = models.JSONField(default=list, blank=True)
    supported_power_sources = models.JSONField(default=list, blank=True)
    returned_data_fields = models.JSONField(default=list, blank=True)
    payload_mapping = models.JSONField(default=dict, blank=True)
    display_schema = models.JSONField(default=dict, blank=True)
    supported_widgets = models.JSONField(default=list, blank=True)
    commands_schema = models.JSONField(default=list, blank=True)
    capabilities = models.JSONField(default=list, blank=True)
    sample_payload = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sensor_catalogs"
        ordering = ["code"]

    def __str__(self):
        return self.name


class FarmDevice(models.Model):
    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False, db_index=True)
    farm = models.ForeignKey("farm_hub.FarmHub", on_delete=models.CASCADE, related_name="sensors")
    sensor_catalog = models.ForeignKey(
        DeviceCatalog,
        on_delete=models.PROTECT,
        related_name="farm_devices",
        null=True,
        blank=True,
    )
    device_catalogs = models.ManyToManyField(
        DeviceCatalog,
        related_name="composite_farm_devices",
        blank=True,
    )
    physical_device_uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    sensor_type = models.CharField(max_length=255, blank=True, default="")
    cluster_uuid = models.UUIDField(null=True, blank=True, db_index=True)
    location_metadata = models.JSONField(default=dict, blank=True)
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

    def get_device_catalogs(self):
        catalogs = list(self.device_catalogs.all())
        if catalogs:
            return catalogs
        if self.sensor_catalog_id:
            return [self.sensor_catalog]
        return []

    def get_device_catalog_by_code(self, code):
        if not code:
            return None
        normalized_code = str(code).strip().lower()
        for catalog in self.get_device_catalogs():
            if catalog.code.lower() == normalized_code:
                return catalog
        return None

    def get_sensor_key(self):
        if self.sensor_catalog and self.sensor_catalog.code:
            return self.sensor_catalog.code
        return "sensor-7-1"

    def get_ai_device_key(self):
        return f"device:{self.physical_device_uuid}"


class SensorExternalRequestLog(models.Model):
    farm_uuid = models.UUIDField(db_index=True)
    sensor_catalog_uuid = models.UUIDField(null=True, blank=True, db_index=True)
    physical_device_uuid = models.UUIDField(db_index=True)
    cluster_uuid = models.UUIDField(null=True, blank=True, db_index=True)
    location_metadata = models.JSONField(default=dict, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sensor_external_request_logs"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.physical_device_uuid}:{self.created_at.isoformat()}"
