from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("device_hub", "0006_rename_sensorcatalog_to_devicecatalog_and_add_communication_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="devicecatalog",
            name="capabilities",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="devicecatalog",
            name="commands_schema",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="devicecatalog",
            name="display_schema",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="devicecatalog",
            name="payload_mapping",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="devicecatalog",
            name="supported_widgets",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
