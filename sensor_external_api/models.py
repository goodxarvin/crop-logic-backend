from django.db import models


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
