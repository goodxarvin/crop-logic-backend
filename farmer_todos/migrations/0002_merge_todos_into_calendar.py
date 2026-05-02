from django.db import migrations


def forwards(apps, schema_editor):
    TodoZone = apps.get_model("farmer_todos", "FarmerTodoZone")
    TodoTag = apps.get_model("farmer_todos", "FarmerTodoTag")
    TodoTask = apps.get_model("farmer_todos", "FarmerTodoTask")
    CalendarZone = apps.get_model("farmer_calendar", "FarmerCalendarZone")
    CalendarTag = apps.get_model("farmer_calendar", "FarmerCalendarTag")
    CalendarEvent = apps.get_model("farmer_calendar", "FarmerCalendarEvent")

    zone_map = {}
    for todo_zone in TodoZone.objects.all().iterator():
        calendar_zone, _ = CalendarZone.objects.get_or_create(
            farm_id=todo_zone.farm_id,
            value=todo_zone.value,
            defaults={
                "uuid": todo_zone.uuid,
                "label": todo_zone.label,
                "is_active": todo_zone.is_active,
                "created_at": todo_zone.created_at,
                "updated_at": todo_zone.updated_at,
            },
        )
        updated = False
        if calendar_zone.label != todo_zone.label:
            calendar_zone.label = todo_zone.label
            updated = True
        if calendar_zone.is_active != todo_zone.is_active:
            calendar_zone.is_active = todo_zone.is_active
            updated = True
        if updated:
            calendar_zone.save(update_fields=["label", "is_active", "updated_at"])
        zone_map[todo_zone.id] = calendar_zone

    tag_map = {}
    for todo_tag in TodoTag.objects.all().iterator():
        calendar_tag, _ = CalendarTag.objects.get_or_create(
            farm_id=todo_tag.farm_id,
            value=todo_tag.value,
            defaults={
                "uuid": todo_tag.uuid,
                "label": todo_tag.label,
                "is_active": todo_tag.is_active,
                "created_at": todo_tag.created_at,
                "updated_at": todo_tag.updated_at,
            },
        )
        updated = False
        if calendar_tag.label != todo_tag.label:
            calendar_tag.label = todo_tag.label
            updated = True
        if calendar_tag.is_active != todo_tag.is_active:
            calendar_tag.is_active = todo_tag.is_active
            updated = True
        if updated:
            calendar_tag.save(update_fields=["label", "is_active", "updated_at"])
        tag_map[todo_tag.id] = calendar_tag

    through_model = TodoTask.tags.through
    task_tags = {}
    for relation in through_model.objects.all().iterator():
        task_tags.setdefault(relation.farmertodotask_id, []).append(relation.farmertodotag_id)

    for todo_task in TodoTask.objects.all().iterator():
        calendar_event, created = CalendarEvent.objects.get_or_create(
            farm_id=todo_task.farm_id,
            title=todo_task.title,
            scheduled_date=todo_task.scheduled_date,
            time=todo_task.time,
            defaults={
                "zone": zone_map.get(todo_task.zone_id),
                "description": todo_task.note,
                "priority": todo_task.priority,
                "status": todo_task.status,
                "created_at": todo_task.created_at,
                "updated_at": todo_task.updated_at,
            },
        )
        if not created:
            calendar_event.zone = zone_map.get(todo_task.zone_id)
            calendar_event.description = todo_task.note
            calendar_event.priority = todo_task.priority
            calendar_event.status = todo_task.status
            calendar_event.save(update_fields=["zone", "description", "priority", "status", "updated_at"])

        calendar_tags = [tag_map[tag_id] for tag_id in task_tags.get(todo_task.id, []) if tag_id in tag_map]
        if calendar_tags:
            calendar_event.tags.set(calendar_tags)


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("farmer_calendar", "0001_initial"),
        ("farmer_todos", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
