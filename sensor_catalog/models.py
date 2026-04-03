import uuid

from django.db import models


class SensorCatalog(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
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
