from django.db import models

from farm_hub.models import FarmHub


class FarmDashboardConfig(models.Model):
    farm = models.OneToOneField(
        FarmHub,
        on_delete=models.CASCADE,
        related_name="dashboard_config",
    )
    disabled_card_ids = models.JSONField(default=list, blank=True)
    row_order = models.JSONField(default=list, blank=True)
    enable_drag_reorder = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "farm_dashboard_configs"
        ordering = ["-updated_at", "-id"]

    def __str__(self):
        return f"Dashboard config for {self.farm.name}"
