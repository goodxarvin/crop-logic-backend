from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("device_hub", "0004_absorb_sensor_catalog"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.RenameModel(
                    old_name="FarmSensor",
                    new_name="FarmDevice",
                ),
            ],
        ),
    ]
