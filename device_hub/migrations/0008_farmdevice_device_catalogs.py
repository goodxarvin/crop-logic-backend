from django.db import migrations, models


def copy_sensor_catalog_to_device_catalogs(apps, schema_editor):
    FarmDevice = apps.get_model("device_hub", "FarmDevice")
    for farm_device in FarmDevice.objects.exclude(sensor_catalog__isnull=True).iterator():
        farm_device.device_catalogs.add(farm_device.sensor_catalog_id)


class Migration(migrations.Migration):

    dependencies = [
        ("device_hub", "0007_devicecatalog_dynamic_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="farmdevice",
            name="device_catalogs",
            field=models.ManyToManyField(blank=True, related_name="composite_farm_devices", to="device_hub.devicecatalog"),
        ),
        migrations.RunPython(copy_sensor_catalog_to_device_catalogs, migrations.RunPython.noop),
    ]
