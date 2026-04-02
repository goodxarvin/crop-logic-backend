from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("plant", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="plant",
            name="health_profile",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text=(
                    "پروفایل سلامت گیاه برای KPIها. ساختار نمونه: "
                    '{"moisture": {"ideal_value": 65, "min_range": 45, "max_range": 75, "weight": 0.4}}'
                ),
            ),
        ),
    ]
