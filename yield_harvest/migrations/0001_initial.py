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
            name="YieldHarvestPredictionLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("uuid", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ("yield_stats", models.CharField(blank=True, default="", max_length=64)),
                ("yield_chip_text", models.CharField(blank=True, default="", max_length=32)),
                ("harvest_date", models.DateField(blank=True, null=True)),
                ("days_until_harvest", models.IntegerField(blank=True, null=True)),
                ("optimal_window_start", models.DateField(blank=True, null=True)),
                ("optimal_window_end", models.DateField(blank=True, null=True)),
                ("chart_data", models.JSONField(blank=True, default=dict)),
                ("fetched_at", models.DateTimeField(auto_now_add=True)),
                (
                    "farm",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="yield_harvest_predictions",
                        to="farm_hub.farmhub",
                    ),
                ),
            ],
            options={
                "db_table": "yield_harvest_prediction_logs",
                "ordering": ["-fetched_at"],
            },
        ),
    ]
