from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("plant", "0003_plant_irrigation_profile"),
    ]

    operations = [
        migrations.AddField(
            model_name="plant",
            name="growth_profile",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text=(
                    "پروفایل رشد گیاه برای مدل GDD. "
                    '{"base_temperature": 10, "required_gdd_for_maturity": 1200, '
                    '"stage_thresholds": {"flowering": 500, "fruiting": 850}, "current_cumulative_gdd": 320}'
                ),
            ),
        ),
    ]
