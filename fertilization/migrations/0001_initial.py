import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("farm_hub", "0002_seed_default_catalog"),
    ]

    operations = [
        migrations.CreateModel(
            name="FertilizationRecommendationRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("uuid", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ("crop_id", models.CharField(blank=True, default="", max_length=255)),
                ("growth_stage", models.CharField(blank=True, default="", max_length=255)),
                ("task_id", models.CharField(blank=True, db_index=True, default="", max_length=255)),
                ("status", models.CharField(blank=True, default="", max_length=64)),
                ("request_payload", models.JSONField(blank=True, default=dict)),
                ("response_payload", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "farm",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="fertilizations",
                        to="farm_hub.farmhub",
                    ),
                ),
            ],
            options={
                "db_table": "fertilization_requests",
                "ordering": ["-created_at", "-id"],
            },
        ),
    ]
