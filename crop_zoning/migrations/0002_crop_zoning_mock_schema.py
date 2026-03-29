from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("crop_zoning", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CropProduct",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("product_id", models.CharField(max_length=64, unique=True)),
                ("label", models.CharField(max_length=255)),
                ("color", models.CharField(max_length=32)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "crop_products",
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="CropZoneCultivationRiskLayer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("level", models.CharField(choices=[("low", "Low"), ("medium", "Medium"), ("high", "High")], max_length=16)),
                ("color", models.CharField(max_length=32)),
                ("crop_zone", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="cultivation_risk_layer", to="crop_zoning.cropzone")),
            ],
            options={
                "db_table": "crop_zone_cultivation_risk_layers",
                "ordering": ["crop_zone_id"],
            },
        ),
        migrations.CreateModel(
            name="CropZoneRecommendation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("match_percent", models.PositiveIntegerField()),
                ("water_need", models.CharField(max_length=128)),
                ("estimated_profit", models.CharField(max_length=128)),
                ("reason", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("crop_zone", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="recommendation", to="crop_zoning.cropzone")),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="zone_recommendations", to="crop_zoning.cropproduct")),
            ],
            options={
                "db_table": "crop_zone_recommendations",
                "ordering": ["crop_zone_id"],
            },
        ),
        migrations.CreateModel(
            name="CropZoneSoilQualityLayer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("level", models.CharField(choices=[("low", "Low"), ("medium", "Medium"), ("high", "High")], max_length=16)),
                ("score", models.PositiveIntegerField()),
                ("color", models.CharField(max_length=32)),
                ("crop_zone", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="soil_quality_layer", to="crop_zoning.cropzone")),
            ],
            options={
                "db_table": "crop_zone_soil_quality_layers",
                "ordering": ["crop_zone_id"],
            },
        ),
        migrations.CreateModel(
            name="CropZoneWaterNeedLayer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("level", models.CharField(choices=[("low", "Low"), ("medium", "Medium"), ("high", "High")], max_length=16)),
                ("value", models.CharField(max_length=128)),
                ("color", models.CharField(max_length=32)),
                ("crop_zone", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="water_need_layer", to="crop_zoning.cropzone")),
            ],
            options={
                "db_table": "crop_zone_water_need_layers",
                "ordering": ["crop_zone_id"],
            },
        ),
        migrations.CreateModel(
            name="CropZoneCriteria",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=128)),
                ("value", models.PositiveIntegerField()),
                ("sequence", models.PositiveIntegerField(default=0)),
                ("recommendation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="criteria", to="crop_zoning.cropzonerecommendation")),
            ],
            options={
                "db_table": "crop_zone_criteria",
                "ordering": ["sequence", "id"],
            },
        ),
    ]
