from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("device_hub", "0001_initial"),
        ("farm_hub", "0009_farmhub_irrigation_method_fields"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.DeleteModel(name="FarmSensor"),
            ],
        ),
    ]
