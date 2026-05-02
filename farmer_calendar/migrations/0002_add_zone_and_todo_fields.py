import uuid

import django.db.models.deletion
from django.db import migrations, models


def _table_exists(connection, table_name):
    with connection.cursor() as cursor:
        return table_name in connection.introspection.table_names(cursor)


def _column_names(connection, table_name):
    with connection.cursor() as cursor:
        description = connection.introspection.get_table_description(cursor, table_name)
    return {column.name for column in description}


def _constraint_names(connection, table_name):
    with connection.cursor() as cursor:
        constraints = connection.introspection.get_constraints(cursor, table_name)
    return set(constraints.keys())


def sync_farmer_calendar_schema(apps, schema_editor):
    connection = schema_editor.connection
    zone_table = "farmer_calendar_zones"
    event_table = "farmer_calendar_events"

    if not _table_exists(connection, zone_table):
        schema_editor.execute(
            """
            CREATE TABLE farmer_calendar_zones (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                uuid CHAR(32) NOT NULL UNIQUE,
                label VARCHAR(255) NOT NULL,
                value VARCHAR(255) NOT NULL,
                is_active BOOL NOT NULL DEFAULT TRUE,
                created_at DATETIME(6) NOT NULL,
                updated_at DATETIME(6) NOT NULL,
                farm_id BIGINT NOT NULL,
                CONSTRAINT farmer_calendar_zones_farm_id_fk
                    FOREIGN KEY (farm_id) REFERENCES farm_hubs (id)
            )
            """
        )

    zone_constraints = _constraint_names(connection, zone_table)
    if "uniq_farmer_calendar_zone_per_farm" not in zone_constraints:
        schema_editor.execute(
            """
            ALTER TABLE farmer_calendar_zones
            ADD CONSTRAINT uniq_farmer_calendar_zone_per_farm UNIQUE (farm_id, value)
            """
        )

    event_columns = _column_names(connection, event_table)
    if "priority" not in event_columns:
        schema_editor.execute(
            """
            ALTER TABLE farmer_calendar_events
            ADD COLUMN priority VARCHAR(16) NULL
            """
        )
    if "scheduled_date" not in event_columns:
        schema_editor.execute(
            """
            ALTER TABLE farmer_calendar_events
            ADD COLUMN scheduled_date DATE NULL
            """
        )
    if "status" not in event_columns:
        schema_editor.execute(
            """
            ALTER TABLE farmer_calendar_events
            ADD COLUMN status VARCHAR(16) NOT NULL DEFAULT 'open'
            """
        )
    if "time" not in event_columns:
        schema_editor.execute(
            """
            ALTER TABLE farmer_calendar_events
            ADD COLUMN time TIME NULL
            """
        )
    if "zone_id" not in event_columns:
        schema_editor.execute(
            """
            ALTER TABLE farmer_calendar_events
            ADD COLUMN zone_id BIGINT NULL
            """
        )
        schema_editor.execute(
            """
            ALTER TABLE farmer_calendar_events
            ADD CONSTRAINT farmer_calendar_events_zone_id_fk
                FOREIGN KEY (zone_id) REFERENCES farmer_calendar_zones (id)
            """
        )

    schema_editor.execute(
        """
        ALTER TABLE farmer_calendar_events
        MODIFY COLUMN start DATETIME(6) NULL
        """
    )
    schema_editor.execute(
        """
        ALTER TABLE farmer_calendar_events
        MODIFY COLUMN end DATETIME(6) NULL
        """
    )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("farmer_calendar", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(sync_farmer_calendar_schema, noop_reverse),
            ],
            state_operations=[
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
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="calendar_zones",
                                to="farm_hub.farmhub",
                            ),
                        ),
                    ],
                    options={
                        "db_table": "farmer_calendar_zones",
                        "ordering": ["label"],
                    },
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
            ],
        ),
    ]
