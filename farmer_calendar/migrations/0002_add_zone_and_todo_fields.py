import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("farmer_calendar", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="FarmerCalendarZone",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("uuid", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ("label", models.CharField(max_length=255)),
                ("value", models.CharField(max_length=255)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "farm",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="calendar_zones", to="farm_hub.farmhub"),
                ),
            ],
            options={
                "db_table": "farmer_calendar_zones",
                "ordering": ["label"],
            },
        ),
        migrations.AddField(
            model_name="farmercalendarevent",
            name="deadline",
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="farmercalendarevent",
            name="priority",
            field=models.CharField(
                blank=True,
                choices=[("زیاد", "High"), ("متوسط", "Medium"), ("کم", "Low")],
                max_length=16,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="farmercalendarevent",
            name="scheduled_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="farmercalendarevent",
            name="status",
            field=models.CharField(choices=[("open", "Open"), ("done", "Done")], default="open", max_length=16),
        ),
        migrations.AddField(
            model_name="farmercalendarevent",
            name="time",
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="farmercalendarevent",
            name="zone",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="events",
                to="farmer_calendar.farmercalendarzone",
            ),
        ),
        migrations.AlterField(
            model_name="farmercalendarevent",
            name="end",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="farmercalendarevent",
            name="start",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterModelOptions(
            name="farmercalendarevent",
            options={"db_table": "farmer_calendar_events", "ordering": ["scheduled_date", "start", "time", "created_at"]},
        ),
        migrations.AddConstraint(
            model_name="farmercalendarzone",
            constraint=models.UniqueConstraint(fields=("farm", "value"), name="uniq_farmer_calendar_zone_per_farm"),
        ),
    ]
