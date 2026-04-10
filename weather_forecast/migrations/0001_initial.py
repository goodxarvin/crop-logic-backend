import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("farm_hub", "0007_farmhub_subscription_plan"),
    ]

    operations = [
        migrations.CreateModel(
            name="WeatherForecastLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("uuid", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ("condition", models.CharField(blank=True, default="", max_length=128)),
                ("temperature", models.FloatField(blank=True, null=True)),
                ("unit", models.CharField(blank=True, default="°C", max_length=16)),
                ("humidity", models.IntegerField(blank=True, null=True)),
                ("wind_speed", models.FloatField(blank=True, null=True)),
                ("wind_unit", models.CharField(blank=True, default="km/h", max_length=16)),
                ("chart_data", models.JSONField(blank=True, default=dict)),
                ("fetched_at", models.DateTimeField(auto_now_add=True)),
                (
                    "farm",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="weather_forecasts",
                        to="farm_hub.farmhub",
                    ),
                ),
            ],
            options={
                "db_table": "weather_forecast_logs",
                "ordering": ["-fetched_at"],
            },
        ),
    ]
