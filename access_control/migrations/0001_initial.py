from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("farm_hub", "0006_seed_expanded_product_catalog"),
        ("device_hub", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AccessFeature",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("uuid", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ("code", models.CharField(db_index=True, max_length=150, unique=True)),
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, default="")),
                ("feature_type", models.CharField(choices=[("page", "Page"), ("widget", "Widget"), ("action", "Action")], default="page", max_length=32)),
                ("default_enabled", models.BooleanField(default=False)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "access_features", "ordering": ["name"]},
        ),
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
        migrations.CreateModel(
            name="AccessRule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("uuid", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ("code", models.CharField(db_index=True, max_length=150, unique=True)),
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, default="")),
                ("priority", models.PositiveIntegerField(default=100)),
                ("effect", models.CharField(choices=[("allow", "Allow"), ("deny", "Deny")], default="allow", max_length=16)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("farm_types", models.ManyToManyField(blank=True, related_name="access_rules", to="farm_hub.farmtype")),
                ("features", models.ManyToManyField(blank=True, related_name="rules", to="access_control.accessfeature")),
                ("products", models.ManyToManyField(blank=True, related_name="access_rules", to="farm_hub.product")),
                ("sensor_catalogs", models.ManyToManyField(blank=True, related_name="access_rules", to="device_hub.sensorcatalog")),
                ("subscription_plans", models.ManyToManyField(blank=True, related_name="access_rules", to="access_control.subscriptionplan")),
            ],
            options={"db_table": "access_rules", "ordering": ["priority", "name"]},
        ),
    ]
