from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("device_hub", "0009_sync_devicecatalog_schema"),
    ]

    operations = [
        migrations.AddField(
            model_name="farmdevice",
            name="cluster_uuid",
            field=models.UUIDField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="farmdevice",
            name="location_metadata",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="sensorexternalrequestlog",
            name="cluster_uuid",
            field=models.UUIDField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="sensorexternalrequestlog",
            name="location_metadata",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
