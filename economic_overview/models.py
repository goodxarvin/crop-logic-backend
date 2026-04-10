import uuid as uuid_lib

from django.db import models

from farm_hub.models import FarmHub


class EconomicOverviewLog(models.Model):
    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False, db_index=True)
    farm = models.ForeignKey(
        FarmHub,
        on_delete=models.CASCADE,
        related_name="economic_overview_logs",
        null=True,
        blank=True,
    )
    economic_data = models.JSONField(default=list, blank=True)
    chart_series = models.JSONField(default=list, blank=True)
    chart_categories = models.JSONField(default=list, blank=True)
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "economic_overview_logs"
        ordering = ["-fetched_at"]

    def __str__(self):
        farm_label = str(self.farm_id) if self.farm_id else "no-farm"
        return f"{farm_label} — {self.fetched_at}"
