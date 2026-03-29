from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("crop_zoning", "0002_crop_zoning_mock_schema"),
    ]

    operations = [
        migrations.AddField(
            model_name="cropzone",
            name="processing_error",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="cropzone",
            name="processing_status",
            field=models.CharField(
                choices=[("pending", "Pending"), ("processing", "Processing"), ("completed", "Completed"), ("failed", "Failed")],
                default="pending",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="cropzone",
            name="task_id",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.CreateModel(
            name="CropZoneAnalysis",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source", models.CharField(blank=True, default="", max_length=64)),
                ("external_record_id", models.CharField(blank=True, default="", max_length=64)),
                ("latitude", models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ("longitude", models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ("raw_response", models.JSONField(blank=True, default=dict)),
                ("depths", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("crop_zone", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="analysis", to="crop_zoning.cropzone")),
            ],
            options={
                "db_table": "crop_zone_analyses",
                "ordering": ["crop_zone_id"],
            },
        ),
    ]
