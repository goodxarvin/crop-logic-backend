import uuid

import django.db.models.deletion
from django.db import migrations, models


def _create_model_if_missing(app_label, model_name):
    def _operation(apps, schema_editor):
        model = apps.get_model(app_label, model_name)
        existing_tables = set(schema_editor.connection.introspection.table_names())
        if model._meta.db_table in existing_tables:
            return
        schema_editor.create_model(model)

    return _operation


class Migration(migrations.Migration):
    initial = True
    atomic = False

    dependencies = [
        ("farm_hub", "0001_initial"),
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
            ],
        ),
        migrations.RunPython(
            _create_model_if_missing("device_hub", "SensorCatalog"),
            migrations.RunPython.noop,
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name="FarmSensor",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("uuid", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                        ("name", models.CharField(max_length=255)),
                        ("sensor_type", models.CharField(blank=True, default="", max_length=255)),
                        ("is_active", models.BooleanField(default=True)),
                        ("specifications", models.JSONField(blank=True, default=dict)),
                        ("power_source", models.JSONField(blank=True, default=dict)),
                        ("customization", models.JSONField(blank=True, default=dict)),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("updated_at", models.DateTimeField(auto_now=True)),
                        (
                            "farm",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="sensors",
                                to="farm_hub.farmhub",
                            ),
                        ),
                    ],
                    options={"db_table": "farm_sensors", "ordering": ["-created_at"]},
                ),
            ],
        ),
        migrations.RunPython(
            _create_model_if_missing("device_hub", "FarmSensor"),
            migrations.RunPython.noop,
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
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
        migrations.RunPython(
            _create_model_if_missing("device_hub", "SensorExternalRequestLog"),
            migrations.RunPython.noop,
        ),
    ]
