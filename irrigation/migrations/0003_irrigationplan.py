import django.db.models.deletion
import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("irrigation_recommendation", "0002_recommendation_status_and_growth_stage"),
    ]

    operations = [
        migrations.CreateModel(
            name="IrrigationPlan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("uuid", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ("source", models.CharField(choices=[("recommendation", "توصیه هوش مصنوعی"), ("free_text", "متن آزاد کاربر")], db_index=True, max_length=32)),
                ("title", models.CharField(blank=True, default="", max_length=255)),
                ("crop_id", models.CharField(blank=True, default="", max_length=255)),
                ("growth_stage", models.CharField(blank=True, default="", max_length=255)),
                ("plan_payload", models.JSONField(blank=True, default=dict)),
                ("request_payload", models.JSONField(blank=True, default=dict)),
                ("response_payload", models.JSONField(blank=True, default=dict)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "farm",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="irrigation_plans", to="farm_hub.farmhub"),
                ),
                (
                    "recommendation",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="plans", to="irrigation_recommendation.irrigationrecommendationrequest"),
                ),
            ],
            options={
                "db_table": "irrigation_plans",
                "ordering": ["-created_at", "-id"],
            },
        ),
    ]
