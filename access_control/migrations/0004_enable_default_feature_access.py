from django.db import migrations


def enable_default_feature_access(apps, schema_editor):
    AccessFeature = apps.get_model("access_control", "AccessFeature")

    from access_control.catalog import DEFAULT_ACCESS_FEATURES

    default_enabled_codes = [item["code"] for item in DEFAULT_ACCESS_FEATURES if item.get("default_enabled", False)]
    AccessFeature.objects.filter(code__in=default_enabled_codes).update(default_enabled=True)


class Migration(migrations.Migration):
    dependencies = [
        ("access_control", "0003_seed_default_access_rules"),
    ]

    operations = [
        migrations.RunPython(enable_default_feature_access, migrations.RunPython.noop),
    ]
