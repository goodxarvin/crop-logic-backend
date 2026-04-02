import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("farm_hub", "0002_seed_default_catalog"),
    ]

    operations = [
        migrations.CreateModel(
            name="FarmDashboardConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("disabled_card_ids", models.JSONField(blank=True, default=list)),
                ("row_order", models.JSONField(default=list)),
                ("enable_drag_reorder", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "farm",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="dashboard_config",
                        to="farm_hub.farmhub",
                    ),
                ),
            ],
            options={
                "db_table": "farm_dashboard_configs",
                "ordering": ["-updated_at", "-id"],
            },
        ),
    ]
