from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("farm_hub", "0001_initial"),
        ("farm_alerts", "0003_farmalert_tracker_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="FarmAlertTrackerSnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("service_id", models.CharField(default="farm_alerts", max_length=64)),
                ("tracker", models.JSONField(blank=True, default=dict)),
                ("headline", models.CharField(blank=True, default="", max_length=255)),
                ("overview", models.TextField(blank=True, default="")),
                (
                    "status_level",
                    models.CharField(
                        choices=[("info", "Info"), ("warning", "Warning"), ("error", "Error"), ("success", "Success")],
                        default="info",
                        max_length=32,
                    ),
                ),
                ("raw_llm_response", models.TextField(blank=True, default="")),
                ("structured_context", models.JSONField(blank=True, default=dict)),
                ("last_ai_synced_at", models.DateTimeField(blank=True, null=True)),
                ("last_source_update_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "farm",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="alert_tracker_snapshot",
                        to="farm_hub.farmhub",
                    ),
                ),
            ],
            options={
                "db_table": "farm_alert_tracker_snapshots",
            },
        ),
    ]
