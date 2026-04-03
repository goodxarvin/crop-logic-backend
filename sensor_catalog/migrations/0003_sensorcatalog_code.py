import re

from django.db import migrations, models


def _to_snake_case(value):
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", (value or "").strip()).strip("_").lower()
    return normalized or "sensor"


def populate_sensor_codes(apps, schema_editor):
    SensorCatalog = apps.get_model("sensor_catalog", "SensorCatalog")

    used_codes = set()
    for sensor in SensorCatalog.objects.all().order_by("id"):
        base_code = _to_snake_case(sensor.name)
        code = base_code
        suffix = 2
        while code in used_codes:
            code = f"{base_code}_{suffix}"
            suffix += 1
        sensor.code = code
        sensor.save(update_fields=["code"])
        used_codes.add(code)


class Migration(migrations.Migration):
    dependencies = [
        ("sensor_catalog", "0002_sensorcatalog_supported_power_sources"),
    ]

    operations = [
        migrations.AddField(
            model_name="sensorcatalog",
            name="code",
            field=models.CharField(blank=True, db_index=True, default="", max_length=255),
        ),
        migrations.RunPython(populate_sensor_codes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="sensorcatalog",
            name="code",
            field=models.CharField(db_index=True, max_length=255, unique=True),
        ),
    ]
