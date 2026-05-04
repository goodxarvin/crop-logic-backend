import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("device_hub", "0005_rename_farm_sensor_to_farm_device"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="SensorCatalog",
            new_name="DeviceCatalog",
        ),
        migrations.AddField(
            model_name="devicecatalog",
            name="device_communication_type",
            field=models.CharField(
                choices=[("output_only", "Output Only"), ("input_only", "Input Only")],
                db_index=True,
                default="output_only",
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name="farmdevice",
            name="sensor_catalog",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="farm_devices", to="device_hub.devicecatalog"),
        ),
    ]
