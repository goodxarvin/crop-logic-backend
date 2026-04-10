import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("farm_hub", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="FarmAlert",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("uuid", models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)),
                ("farm", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="farm_alerts", to="farm_hub.farmhub")),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, default="")),
                ("color", models.CharField(default="info", max_length=32)),
                ("avatar_icon", models.CharField(blank=True, default="", max_length=64)),
                ("avatar_color", models.CharField(blank=True, default="", max_length=32)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "farm_alerts", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="AnomalyDetection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("uuid", models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)),
                ("farm", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="anomalies", to="farm_hub.farmhub")),
                ("sensor", models.CharField(max_length=255)),
                ("value", models.CharField(max_length=64)),
                ("expected", models.CharField(max_length=64)),
                ("deviation", models.CharField(max_length=64)),
                ("severity", models.CharField(default="warning", max_length=32)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "farm_anomaly_detections", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Recommendation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("uuid", models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)),
                ("farm", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="recommendations", to="farm_hub.farmhub")),
                ("title", models.CharField(max_length=255)),
                ("subtitle", models.TextField(blank=True, default="")),
                ("avatar_icon", models.CharField(blank=True, default="", max_length=64)),
                ("avatar_color", models.CharField(blank=True, default="", max_length=32)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "farm_recommendations", "ordering": ["-created_at"]},
        ),
    ]
