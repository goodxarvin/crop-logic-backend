import json

from django.db import migrations, models


DEFAULT_FARM_TYPE_NAME = "زراعی"


def _table_exists(schema_editor, table_name):
    with schema_editor.connection.cursor() as cursor:
        existing_tables = set(schema_editor.connection.introspection.table_names(cursor))
    return table_name in existing_tables


def _deserialize_json(value):
    if value in (None, "", b""):
        return {}
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return {}


def migrate_plant_rows_to_products(apps, schema_editor):
    if not _table_exists(schema_editor, "plant_plant"):
        return

    FarmType = apps.get_model("farm_hub", "FarmType")
    Product = apps.get_model("farm_hub", "Product")

    farm_type, _ = FarmType.objects.get_or_create(name=DEFAULT_FARM_TYPE_NAME)

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                name,
                light,
                watering,
                soil,
                temperature,
                planting_season,
                harvest_time,
                spacing,
                fertilizer,
                health_profile,
                irrigation_profile,
                growth_profile,
                created_at,
                updated_at
            FROM plant_plant
            """
        )
        columns = [column[0] for column in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

    for row in rows:
        Product.objects.update_or_create(
            farm_type=farm_type,
            name=row["name"],
            defaults={
                "light": row["light"] or "",
                "watering": row["watering"] or "",
                "soil": row["soil"] or "",
                "temperature": row["temperature"] or "",
                "planting_season": row["planting_season"] or "",
                "harvest_time": row["harvest_time"] or "",
                "spacing": row["spacing"] or "",
                "fertilizer": row["fertilizer"] or "",
                "health_profile": _deserialize_json(row["health_profile"]),
                "irrigation_profile": _deserialize_json(row["irrigation_profile"]),
                "growth_profile": _deserialize_json(row["growth_profile"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            },
        )


def drop_legacy_plant_table(apps, schema_editor):
    if _table_exists(schema_editor, "plant_plant"):
        schema_editor.execute("DROP TABLE plant_plant")


class Migration(migrations.Migration):
    dependencies = [
        ("farm_hub", "0004_remove_customization_add_current_crop_area"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="fertilizer",
            field=models.CharField(blank=True, default="", help_text="کود مناسب", max_length=255),
        ),
        migrations.AddField(
            model_name="product",
            name="growth_profile",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='پروفایل رشد محصول برای مدل GDD. {"base_temperature": 10, "required_gdd_for_maturity": 1200, "stage_thresholds": {"flowering": 500, "fruiting": 850}, "current_cumulative_gdd": 320}',
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="harvest_time",
            field=models.CharField(blank=True, default="", help_text="زمان برداشت", max_length=255),
        ),
        migrations.AddField(
            model_name="product",
            name="health_profile",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='پروفایل سلامت محصول برای KPIها. ساختار نمونه: {"moisture": {"ideal_value": 65, "min_range": 45, "max_range": 75, "weight": 0.4}}',
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="irrigation_profile",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='پروفایل آبیاری محصول برای محاسبات ETc. {"kc_initial": 0.6, "kc_mid": 1.15, "kc_end": 0.8, "growth_stage_duration": {"initial": 20, "mid": 30, "late": 25}}',
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="light",
            field=models.CharField(blank=True, default="", help_text="نور مورد نیاز", max_length=255),
        ),
        migrations.AddField(
            model_name="product",
            name="planting_season",
            field=models.CharField(blank=True, default="", help_text="فصل کاشت", max_length=255),
        ),
        migrations.AddField(
            model_name="product",
            name="soil",
            field=models.CharField(blank=True, default="", help_text="خاک مناسب", max_length=255),
        ),
        migrations.AddField(
            model_name="product",
            name="spacing",
            field=models.CharField(blank=True, default="", help_text="فاصله کاشت", max_length=255),
        ),
        migrations.AddField(
            model_name="product",
            name="temperature",
            field=models.CharField(blank=True, default="", help_text="دمای مناسب", max_length=255),
        ),
        migrations.AddField(
            model_name="product",
            name="watering",
            field=models.CharField(blank=True, default="", help_text="آبیاری", max_length=255),
        ),
        migrations.RunPython(migrate_plant_rows_to_products, migrations.RunPython.noop),
        migrations.RunPython(drop_legacy_plant_table, migrations.RunPython.noop),
    ]
