import uuid as uuid_lib

from django.db import models

from farm_hub.models import FarmHub


class WeatherForecastLog(models.Model):
    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False, db_index=True)
    farm = models.ForeignKey(
        FarmHub,
        on_delete=models.CASCADE,
        related_name="weather_forecasts",
        null=True,
        blank=True,
    )
    condition = models.CharField(max_length=128, blank=True, default="")
    temperature = models.FloatField(null=True, blank=True)
    unit = models.CharField(max_length=16, blank=True, default="°C")
    humidity = models.IntegerField(null=True, blank=True)
    wind_speed = models.FloatField(null=True, blank=True)
    wind_unit = models.CharField(max_length=16, blank=True, default="km/h")
    chart_data = models.JSONField(default=dict, blank=True)
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "weather_forecast_logs"
        ordering = ["-fetched_at"]

    def __str__(self):
        farm_label = str(self.farm_id) if self.farm_id else "no-farm"
        return f"{farm_label} — {self.condition} {self.temperature}{self.unit}"
