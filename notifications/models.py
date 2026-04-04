import uuid as uuid_lib

from django.db import models


class FarmNotification(models.Model):
    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False, db_index=True)
    farm = models.ForeignKey(
        "farm_hub.FarmHub",
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    level = models.CharField(max_length=32, default="info")
    is_read = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "farm_notifications"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.farm_id}:{self.title}"
