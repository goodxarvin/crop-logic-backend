from django.db import migrations


FARM_TYPES = {
    "زراعی": ["گندم", "ذرت"],
    "درختی": ["سیب", "پسته"],
    "غرقابی": ["برنج"],
}


def seed_catalog(apps, schema_editor):
    FarmType = apps.get_model("farm_hub", "FarmType")
    Product = apps.get_model("farm_hub", "Product")

    for farm_type_name, products in FARM_TYPES.items():
        farm_type, _ = FarmType.objects.get_or_create(name=farm_type_name)
        for product_name in products:
            Product.objects.get_or_create(farm_type=farm_type, name=product_name)


def unseed_catalog(apps, schema_editor):
    FarmType = apps.get_model("farm_hub", "FarmType")
    FarmType.objects.filter(name__in=FARM_TYPES.keys()).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("farm_hub", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_catalog, unseed_catalog),
    ]
