from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("irrigation", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="irrigationrecommendationrequest",
            name="growth_stage",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AlterField(
            model_name="irrigationrecommendationrequest",
            name="status",
            field=models.CharField(
                choices=[
                    ("in_progress", "در حال اجرا"),
                    ("pending_confirmation", "منتظر تایید"),
                    ("completed", "پایان یافته"),
                    ("error", "خطا"),
                ],
                db_index=True,
                default="pending_confirmation",
                max_length=64,
            ),
        ),
    ]
