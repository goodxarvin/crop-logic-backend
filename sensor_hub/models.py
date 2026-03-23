import uuid

from django.conf import settings
from django.db import models


class Sensor(models.Model):
    uuid_sensor = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sensors",
    )
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    specifications = models.JSONField(default=dict, blank=True)
    power_source = models.JSONField(default=dict, blank=True)
    customized_sensors = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sensors"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.uuid_sensor})"
