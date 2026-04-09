from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("access_control", "0001_initial"),
        ("farm_hub", "0006_seed_expanded_product_catalog"),
    ]

    operations = [
        migrations.CreateModel(
            name="FarmAccessProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("profile_data", models.JSONField(blank=True, default=dict)),
                ("resolved_from_profile", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("farm", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="access_profile", to="farm_hub.farmhub")),
                ("subscription_plan", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="farm_access_profiles", to="access_control.subscriptionplan")),
            ],
            options={"db_table": "farm_access_profiles", "ordering": ["-updated_at"]},
        ),
    ]
