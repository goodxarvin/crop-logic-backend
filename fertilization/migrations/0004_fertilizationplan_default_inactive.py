from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("fertilization_recommendation", "0003_fertilizationplan"),
    ]

    operations = [
        migrations.AlterField(
            model_name="fertilizationplan",
            name="is_active",
            field=models.BooleanField(db_index=True, default=False),
        ),
    ]
