import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("device_hub", "0003_absorb_sensor_external_api"),
        ("farm_hub", "0003_farmsensor_catalog_and_physical_device"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name="farmsensor",
                    name="physical_device_uuid",
                    field=models.UUIDField(db_index=True, default=uuid.uuid4, unique=True),
                ),
                migrations.AddField(
                    model_name="farmsensor",
                    name="sensor_catalog",
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="farm_sensors",
                        to="device_hub.sensorcatalog",
                    ),
                ),
            ],
        ),
    ]
