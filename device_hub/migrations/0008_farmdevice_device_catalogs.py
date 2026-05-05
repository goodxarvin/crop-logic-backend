from django.db import migrations, models


def ensure_device_catalogs_m2m_table(apps, schema_editor):
    FarmDevice = apps.get_model("device_hub", "FarmDevice")
    through_model = FarmDevice._meta.get_field("device_catalogs").remote_field.through
    existing_tables = set(schema_editor.connection.introspection.table_names())
    if through_model._meta.db_table not in existing_tables:
        schema_editor.create_model(through_model)


def copy_sensor_catalog_to_device_catalogs(apps, schema_editor):
    FarmDevice = apps.get_model("device_hub", "FarmDevice")
    through_model = FarmDevice._meta.get_field("device_catalogs").remote_field.through
    through_table = through_model._meta.db_table
    farm_device_column = through_model._meta.get_field("farmdevice").column
    device_catalog_column = through_model._meta.get_field("devicecatalog").column

    with schema_editor.connection.cursor() as cursor:
        for farm_device_id, sensor_catalog_id in FarmDevice.objects.exclude(sensor_catalog__isnull=True).values_list("pk", "sensor_catalog_id").iterator():
            cursor.execute(
                f"""
                INSERT IGNORE INTO {schema_editor.quote_name(through_table)}
                ({schema_editor.quote_name(farm_device_column)}, {schema_editor.quote_name(device_catalog_column)})
                VALUES (%s, %s)
                """,
                [farm_device_id, sensor_catalog_id],
            )


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("device_hub", "0007_devicecatalog_dynamic_fields"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name="farmdevice",
                    name="device_catalogs",
                    field=models.ManyToManyField(blank=True, related_name="composite_farm_devices", to="device_hub.devicecatalog"),
                ),
            ],
        ),
        migrations.RunPython(ensure_device_catalogs_m2m_table, migrations.RunPython.noop),
        migrations.RunPython(copy_sensor_catalog_to_device_catalogs, migrations.RunPython.noop),
    ]
