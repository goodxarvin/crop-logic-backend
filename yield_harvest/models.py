import uuid as uuid_lib

from django.db import models

from farm_hub.models import FarmHub


class YieldHarvestPredictionLog(models.Model):
    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False, db_index=True)
    farm = models.ForeignKey(
        FarmHub,
        on_delete=models.CASCADE,
        related_name="yield_harvest_predictions",
        null=True,
        blank=True,
    )
    yield_stats = models.CharField(max_length=64, blank=True, default="")
    yield_chip_text = models.CharField(max_length=32, blank=True, default="")
    harvest_date = models.DateField(null=True, blank=True)
    days_until_harvest = models.IntegerField(null=True, blank=True)
    optimal_window_start = models.DateField(null=True, blank=True)
    optimal_window_end = models.DateField(null=True, blank=True)
    chart_data = models.JSONField(default=dict, blank=True)
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "yield_harvest_prediction_logs"
        ordering = ["-fetched_at"]

    def __str__(self):
        farm_label = str(self.farm_id) if self.farm_id else "no-farm"
        return f"{farm_label} — {self.yield_stats} harvest:{self.harvest_date}"
