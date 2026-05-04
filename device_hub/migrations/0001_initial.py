import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("farm_hub", "0009_farmhub_irrigation_method_fields"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name="SensorCatalog",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("uuid", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                        ("code", models.CharField(db_index=True, max_length=255, unique=True)),
                        ("name", models.CharField(db_index=True, max_length=255, unique=True)),
                        ("description", models.TextField(blank=True, default="")),
                        ("customizable_fields", models.JSONField(blank=True, default=list)),
                        ("supported_power_sources", models.JSONField(blank=True, default=list)),
                        ("returned_data_fields", models.JSONField(blank=True, default=list)),
                        ("sample_payload", models.JSONField(blank=True, default=dict)),
                        ("is_active", models.BooleanField(default=True)),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("updated_at", models.DateTimeField(auto_now=True)),
                    ],
                    options={"db_table": "sensor_catalogs", "ordering": ["code"]},
                ),
                migrations.CreateModel(
                    name="FarmSensor",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("uuid", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                        ("physical_device_uuid", models.UUIDField(db_index=True, default=uuid.uuid4, unique=True)),
                        ("name", models.CharField(max_length=255)),
                        ("sensor_type", models.CharField(blank=True, default="", max_length=255)),
                        ("is_active", models.BooleanField(default=True)),
                        ("specifications", models.JSONField(blank=True, default=dict)),
                        ("power_source", models.JSONField(blank=True, default=dict)),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("updated_at", models.DateTimeField(auto_now=True)),
                        ("farm", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sensors", to="farm_hub.farmhub")),
                        ("sensor_catalog", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="farm_sensors", to="device_hub.sensorcatalog")),
                    ],
                    options={"db_table": "farm_sensors", "ordering": ["-created_at"]},
                ),
                migrations.CreateModel(
                    name="SensorExternalRequestLog",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("farm_uuid", models.UUIDField(db_index=True)),
                        ("sensor_catalog_uuid", models.UUIDField(blank=True, db_index=True, null=True)),
                        ("physical_device_uuid", models.UUIDField(db_index=True)),
                        ("payload", models.JSONField(blank=True, default=dict)),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                    ],
                    options={"db_table": "sensor_external_request_logs", "ordering": ["-created_at", "-id"]},
                ),
            ],
        ),
    ]
