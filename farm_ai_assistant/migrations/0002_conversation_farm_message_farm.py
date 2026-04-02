import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("farm_hub", "0002_seed_default_catalog"),
        ("farm_ai_assistant", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="conversation",
            name="farm",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="ai_conversations",
                to="farm_hub.farmhub",
            ),
        ),
        migrations.AddField(
            model_name="message",
            name="farm",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="ai_messages",
                to="farm_hub.farmhub",
            ),
        ),
    ]
