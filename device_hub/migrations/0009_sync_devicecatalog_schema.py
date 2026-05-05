from django.db import migrations, models


def add_column_if_missing(schema_editor, table_name, column_name, field):
    existing_columns = {
        column.name
        for column in schema_editor.connection.introspection.get_table_description(
            schema_editor.connection.cursor(),
            table_name,
        )
    }
    if column_name in existing_columns:
        return
    field.set_attributes_from_name(column_name)
    schema_editor.add_field(
        field.model,
        field,
    )


def sync_devicecatalog_schema(apps, schema_editor):
    DeviceCatalog = apps.get_model("device_hub", "DeviceCatalog")
    table_name = DeviceCatalog._meta.db_table

    fields = [
        DeviceCatalog._meta.get_field("device_communication_type"),
        DeviceCatalog._meta.get_field("payload_mapping"),
        DeviceCatalog._meta.get_field("display_schema"),
        DeviceCatalog._meta.get_field("supported_widgets"),
        DeviceCatalog._meta.get_field("commands_schema"),
        DeviceCatalog._meta.get_field("capabilities"),
    ]

    for field in fields:
        add_column_if_missing(schema_editor, table_name, field.column, field)


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("device_hub", "0008_farmdevice_device_catalogs"),
    ]

    operations = [
        migrations.RunPython(sync_devicecatalog_schema, migrations.RunPython.noop),
    ]
