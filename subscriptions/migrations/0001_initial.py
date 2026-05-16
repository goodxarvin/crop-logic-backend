from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("access_control", "0005_backfill_farm_subscription_plans"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="SubscriptionPlan",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("uuid", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                        ("code", models.CharField(db_index=True, max_length=100, unique=True)),
                        ("name", models.CharField(max_length=255)),
                        ("description", models.TextField(blank=True, default="")),
                        ("metadata", models.JSONField(blank=True, default=dict)),
                        ("is_active", models.BooleanField(default=True)),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("updated_at", models.DateTimeField(auto_now=True)),
                    ],
                    options={"db_table": "access_subscription_plans", "ordering": ["name"]},
                ),
            ],
            database_operations=[],
        ),
    ]
