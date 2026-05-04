from __future__ import annotations

from datetime import date, datetime, time, timedelta

from django.apps import apps as django_apps
from django.utils import timezone
from django.utils.dateparse import parse_date

AUTO_PLAN_SOURCE = "auto_plan_sync"
PLAN_TYPE_IRRIGATION = "irrigation"
PLAN_TYPE_FERTILIZATION = "fertilization"


def create_event_for_farm(
    *,
    farm,
    title,
    description="",
    start=None,
    end=None,
    scheduled_date=None,
    event_time=None,
    priority=None,
    tags=None,
    zone_value="برنامه خودکار",
    extended_props=None,
):
    FarmerCalendarEvent = django_apps.get_model("farmer_calendar", "FarmerCalendarEvent")
    FarmerCalendarZone = django_apps.get_model("farmer_calendar", "FarmerCalendarZone")
    from .enums import FarmerPriority

    if priority is None:
        priority = FarmerPriority.MEDIUM
    zone, _ = FarmerCalendarZone.objects.get_or_create(
        farm=farm,
        value=zone_value,
        defaults={"label": zone_value},
    )
    if zone.label != zone_value:
        zone.label = zone_value
        zone.save(update_fields=["label", "updated_at"])

    payload = dict(extended_props or {})
    payload["tags"] = list(tags or [])

    return FarmerCalendarEvent.objects.create(
        farm=farm,
        zone=zone,
        title=title,
        description=description,
        deadline=int(end.timestamp()) if end else None,
        scheduled_date=scheduled_date,
        time=event_time,
        start=start,
        end=end,
        priority=priority,
        status=FarmerCalendarEvent.STATUS_OPEN,
        extended_props=payload,
    )


def delete_plan_events(*, farm, plan_type, plan_uuid):
    FarmerCalendarEvent = django_apps.get_model("farmer_calendar", "FarmerCalendarEvent")
    for event in FarmerCalendarEvent.objects.filter(farm=farm):
        props = event.extended_props or {}
        if (
            props.get("source") == AUTO_PLAN_SOURCE
            and props.get("plan_type") == plan_type
            and str(props.get("plan_uuid")) == str(plan_uuid)
        ):
            event.delete()


def sync_plan_events(plan, plan_type):
    from .enums import FarmerPriority

    delete_plan_events(farm=plan.farm, plan_type=plan_type, plan_uuid=plan.uuid)

    if getattr(plan, "is_deleted", False) or not getattr(plan, "is_active", False):
        return []

    if plan_type == PLAN_TYPE_IRRIGATION:
        items = _build_irrigation_events(plan)
    elif plan_type == PLAN_TYPE_FERTILIZATION:
        items = _build_fertilization_events(plan)
    else:
        items = []

    created = []
    for index, item in enumerate(items, start=1):
        created.append(
            create_event_for_farm(
                farm=plan.farm,
                title=item["title"],
                description=item.get("description", ""),
                start=item.get("start"),
                end=item.get("end"),
                scheduled_date=item.get("scheduled_date"),
                event_time=item.get("time"),
                priority=item.get("priority", FarmerPriority.MEDIUM),
                tags=item.get("tags", []),
                zone_value=item.get("zone_value", "برنامه خودکار"),
                extended_props={
                    "source": AUTO_PLAN_SOURCE,
                    "plan_type": plan_type,
                    "plan_uuid": str(plan.uuid),
                    "plan_title": plan.title,
                    "entry_index": index,
                    **item.get("extended_props", {}),
                },
            )
        )
    return created


def _build_irrigation_events(plan):
    from .enums import FarmerPriority, FarmerTag

    payload = plan.plan_payload if isinstance(plan.plan_payload, dict) else {}
    plan_data = payload.get("plan") if isinstance(payload.get("plan"), dict) else {}
    water_balance = payload.get("water_balance") if isinstance(payload.get("water_balance"), dict) else {}
    daily_entries = water_balance.get("daily") if isinstance(water_balance.get("daily"), list) else []

    created = []
    for entry in daily_entries:
        if not isinstance(entry, dict):
            continue
        scheduled = _parse_date(entry.get("forecast_date"))
        if not scheduled:
            continue
        start_time, end_time = _parse_time_range(entry.get("irrigation_timing") or plan_data.get("bestTimeOfDay"))
        start, end = _build_datetimes(scheduled, start_time, end_time, default_duration_minutes=plan_data.get("durationMinutes"))
        gross_amount = entry.get("gross_irrigation_mm")
        title = f"آبیاری - {plan.crop_id or plan.title or 'مزرعه'}"
        description_parts = []
        if gross_amount not in (None, ""):
            description_parts.append(f"مقدار آبیاری: {gross_amount} mm")
        if plan_data.get("durationMinutes"):
            description_parts.append(f"مدت زمان: {plan_data.get('durationMinutes')} دقیقه")
        if entry.get("irrigation_timing"):
            description_parts.append(f"بازه اجرا: {entry.get('irrigation_timing')}")
        created.append(
            {
                "title": title,
                "description": " | ".join(description_parts),
                "scheduled_date": scheduled,
                "time": start_time,
                "start": start,
                "end": end,
                "priority": FarmerPriority.HIGH,
                "tags": [FarmerTag.IRRIGATION.value],
                "zone_value": "آبیاری",
                "extended_props": {
                    "kind": "irrigation",
                    "gross_irrigation_mm": gross_amount,
                    "irrigation_timing": entry.get("irrigation_timing"),
                },
            }
        )

    if created:
        return created

    scheduled = timezone.localdate()
    start_time, end_time = _parse_time_range(plan_data.get("bestTimeOfDay"))
    start, end = _build_datetimes(scheduled, start_time, end_time, default_duration_minutes=plan_data.get("durationMinutes"))
    return [
        {
            "title": f"آبیاری - {plan.crop_id or plan.title or 'مزرعه'}",
            "description": f"برنامه فعال آبیاری: {plan.title}".strip(),
            "scheduled_date": scheduled,
            "time": start_time,
            "start": start,
            "end": end,
            "priority": FarmerPriority.HIGH,
            "tags": [FarmerTag.IRRIGATION.value],
            "zone_value": "آبیاری",
            "extended_props": {"kind": "irrigation_fallback"},
        }
    ]


def _build_fertilization_events(plan):
    from .enums import FarmerPriority, FarmerTag

    payload = plan.plan_payload if isinstance(plan.plan_payload, dict) else {}
    primary = payload.get("primary_recommendation") if isinstance(payload.get("primary_recommendation"), dict) else {}
    guide = payload.get("application_guide") if isinstance(payload.get("application_guide"), dict) else {}
    steps = guide.get("steps") if isinstance(guide.get("steps"), list) else []
    interval = primary.get("application_interval") if isinstance(primary.get("application_interval"), dict) else {}
    interval_days = _safe_int(interval.get("value"))

    base_date = timezone.localdate()
    fertilizer_name = primary.get("display_title") or primary.get("fertilizer_name") or plan.title or "برنامه کودی"
    created = []

    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            continue
        scheduled = _extract_step_date(step) or (base_date + timedelta(days=(index * interval_days if interval_days else index)))
        start = timezone.make_aware(datetime.combine(scheduled, time(hour=8, minute=0)))
        end = start + timedelta(minutes=30)
        description = str(step.get("description") or guide.get("safety_warning") or "").strip()
        created.append(
            {
                "title": f"کوددهی - {fertilizer_name}",
                "description": description,
                "scheduled_date": scheduled,
                "time": start.time(),
                "start": start,
                "end": end,
                "priority": FarmerPriority.MEDIUM,
                "tags": [FarmerTag.FERTILIZATION.value],
                "zone_value": "کوددهی",
                "extended_props": {
                    "kind": "fertilization",
                    "step_number": step.get("step_number"),
                    "fertilizer_code": primary.get("fertilizer_code"),
                },
            }
        )

    if created:
        return created

    scheduled = base_date
    start = timezone.make_aware(datetime.combine(scheduled, time(hour=8, minute=0)))
    end = start + timedelta(minutes=30)
    interval_label = interval.get("label") or ""
    description = " | ".join(part for part in [str(primary.get("summary") or "").strip(), str(interval_label).strip()] if part)
    return [
        {
            "title": f"کوددهی - {fertilizer_name}",
            "description": description,
            "scheduled_date": scheduled,
            "time": start.time(),
            "start": start,
            "end": end,
            "priority": FarmerPriority.MEDIUM,
            "tags": [FarmerTag.FERTILIZATION.value],
            "zone_value": "کوددهی",
            "extended_props": {
                "kind": "fertilization_fallback",
                "fertilizer_code": primary.get("fertilizer_code"),
            },
        }
    ]


def _parse_date(value):
    if isinstance(value, date):
        return value
    if not value:
        return None
    return parse_date(str(value))


def _parse_time_range(value):
    if not value:
        return None, None
    raw = str(value).replace("تا", "-").replace("–", "-")
    parts = [part.strip() for part in raw.split("-") if part.strip()]
    if not parts:
        return None, None
    start_time = _parse_time(parts[0])
    end_time = _parse_time(parts[1]) if len(parts) > 1 else None
    return start_time, end_time


def _parse_time(value):
    if isinstance(value, time):
        return value
    if not value:
        return None
    cleaned = str(value).strip()
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(cleaned, fmt).time()
        except ValueError:
            continue
    return None


def _build_datetimes(scheduled, start_time, end_time, default_duration_minutes=None):
    if scheduled is None:
        return None, None
    if start_time is None:
        start_time = time(hour=6, minute=0)
    start = timezone.make_aware(datetime.combine(scheduled, start_time))
    if end_time is not None:
        end = timezone.make_aware(datetime.combine(scheduled, end_time))
    else:
        end = start + timedelta(minutes=_safe_int(default_duration_minutes) or 30)
    return start, end


def _extract_step_date(step):
    for key in ("date", "scheduled_date", "application_date", "target_date", "forecast_date"):
        parsed = _parse_date(step.get(key))
        if parsed:
            return parsed
    return None


def _safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
