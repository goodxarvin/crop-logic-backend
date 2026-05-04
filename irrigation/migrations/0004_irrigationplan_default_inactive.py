from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("irrigation_recommendation", "0003_irrigationplan"),
    ]

    operations = [
        migrations.AlterField(
            model_name="irrigationplan",
            name="is_active",
            field=models.BooleanField(db_index=True, default=False),
        ),
    ]
