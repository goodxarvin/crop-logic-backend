from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("plant", "0002_plant_health_profile"),
    ]

    operations = [
        migrations.AddField(
            model_name="plant",
            name="irrigation_profile",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text=(
                    "پروفایل آبیاری گیاه برای محاسبات ETc. "
                    '{"kc_initial": 0.6, "kc_mid": 1.15, "kc_end": 0.8, '
                    '"growth_stage_duration": {"initial": 20, "mid": 30, "late": 25}}'
                ),
            ),
        ),
    ]
