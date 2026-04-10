from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("farm_hub", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="EconomicOverviewLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("uuid", models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)),
                ("farm", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="economic_overview_logs", to="farm_hub.farmhub")),
                ("economic_data", models.JSONField(blank=True, default=list)),
                ("chart_series", models.JSONField(blank=True, default=list)),
                ("chart_categories", models.JSONField(blank=True, default=list)),
                ("fetched_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "economic_overview_logs", "ordering": ["-fetched_at"]},
        ),
    ]
