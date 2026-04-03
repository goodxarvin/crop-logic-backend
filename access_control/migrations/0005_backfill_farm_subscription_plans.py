from django.db import migrations


def backfill_farm_subscription_plans(apps, schema_editor):
    SubscriptionPlan = apps.get_model("access_control", "SubscriptionPlan")
    FarmHub = apps.get_model("farm_hub", "FarmHub")

    default_plan = (
        SubscriptionPlan.objects.filter(is_active=True, metadata__is_default=True).order_by("name").first()
        or SubscriptionPlan.objects.filter(code="gold", is_active=True).first()
    )
    if default_plan is None:
        return

    FarmHub.objects.filter(subscription_plan__isnull=True).update(subscription_plan=default_plan)


class Migration(migrations.Migration):
    dependencies = [
        ("access_control", "0004_enable_default_feature_access"),
        ("farm_hub", "0007_farmhub_subscription_plan"),
    ]

    operations = [
        migrations.RunPython(backfill_farm_subscription_plans, migrations.RunPython.noop),
    ]
