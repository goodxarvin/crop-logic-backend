from django.db import migrations


CATALOG_SEED_DATA = {
    "زراعی": [
        {"name": "گندم", "planting_season": "پاییز", "harvest_time": "اواخر بهار", "soil": "لومی"},
        {"name": "ذرت", "planting_season": "بهار", "harvest_time": "تابستان", "soil": "لومی شنی"},
        {"name": "جو", "planting_season": "پاییز", "harvest_time": "اواخر بهار", "soil": "لومی"},
        {"name": "کلزا", "planting_season": "پاییز", "harvest_time": "بهار", "soil": "لومی رسی"},
        {"name": "پنبه", "planting_season": "بهار", "harvest_time": "پاییز", "soil": "لومی"},
    ],
    "درختی": [
        {"name": "سیب", "planting_season": "زمستان", "harvest_time": "پاییز", "soil": "لومی"},
        {"name": "پسته", "planting_season": "زمستان", "harvest_time": "اواخر تابستان", "soil": "شنی لومی"},
        {"name": "انگور", "planting_season": "اواخر زمستان", "harvest_time": "تابستان", "soil": "لومی"},
        {"name": "انار", "planting_season": "اواخر زمستان", "harvest_time": "پاییز", "soil": "لومی شنی"},
    ],
    "غرقابی": [
        {"name": "برنج", "planting_season": "بهار", "harvest_time": "اواخر تابستان", "soil": "رسی"},
    ],
    "گلخانه ای": [
        {"name": "گوجه فرنگی", "planting_season": "چهار فصل", "harvest_time": "چند مرحله ای", "soil": "کوکوپیت"},
        {"name": "خیار", "planting_season": "چهار فصل", "harvest_time": "چند مرحله ای", "soil": "پرلیت"},
        {"name": "فلفل دلمه ای", "planting_season": "چهار فصل", "harvest_time": "چند مرحله ای", "soil": "بستر هیدروپونیک"},
    ],
}


def seed_expanded_catalog(apps, schema_editor):
    FarmType = apps.get_model("farm_hub", "FarmType")
    Product = apps.get_model("farm_hub", "Product")

    for farm_type_name, products in CATALOG_SEED_DATA.items():
        farm_type, _ = FarmType.objects.get_or_create(name=farm_type_name)
        for product_data in products:
            Product.objects.update_or_create(
                farm_type=farm_type,
                name=product_data["name"],
                defaults={key: value for key, value in product_data.items() if key != "name"},
            )


def unseed_expanded_catalog(apps, schema_editor):
    FarmType = apps.get_model("farm_hub", "FarmType")
    FarmType.objects.filter(name__in=CATALOG_SEED_DATA.keys()).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("farm_hub", "0005_product_profiles_and_plant_migration"),
    ]

    operations = [
        migrations.RunPython(seed_expanded_catalog, unseed_expanded_catalog),
    ]
