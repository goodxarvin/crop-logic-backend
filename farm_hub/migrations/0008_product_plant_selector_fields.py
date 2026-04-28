from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("farm_hub", "0007_farmhub_subscription_plan"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="growth_stage",
            field=models.CharField(blank=True, default="", help_text="مرحله رشد فعلی", max_length=255),
        ),
        migrations.AddField(
            model_name="product",
            name="growth_stages",
            field=models.JSONField(blank=True, default=list, help_text="فهرست مراحل رشد محصول"),
        ),
        migrations.AddField(
            model_name="product",
            name="icon",
            field=models.CharField(blank=True, default="", help_text="آیکون محصول برای فرانت", max_length=100),
        ),
    ]
