from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("farm_hub", "0008_product_plant_selector_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="farmhub",
            name="irrigation_method_id",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="farmhub",
            name="irrigation_method_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]
