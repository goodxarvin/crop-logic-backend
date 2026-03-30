from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("sensor_hub", "0001_initial"),
        ("crop_zoning", "0003_zone_processing_and_analysis"),
    ]

    operations = [
        migrations.AddField(
            model_name="croparea",
            name="sensor",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="crop_areas",
                to="sensor_hub.sensor",
            ),
        ),
    ]
