import time

from django.db import OperationalError, ProgrammingError
from django.db.models import Case, IntegerField, QuerySet, Value, When


from farm_hub.models import FarmHub

from .models import FarmNotification


DEFAULT_POLL_TIMEOUT_SECONDS = 15
DEFAULT_POLL_INTERVAL_SECONDS = 1


def create_notification_for_farm_uuid(*, farm_uuid, title, message, level="info", metadata=None):
    farm = FarmHub.objects.filter(farm_uuid=farm_uuid).first()
    if farm is None:
        raise ValueError("Farm not found.")

    try:
        return FarmNotification.objects.create(
            farm=farm,
            title=title,
            message=message,
            level=level,
            metadata=metadata or {},
        )
    except (ProgrammingError, OperationalError) as exc:
        raise ValueError("Notifications table is not migrated.") from exc


def get_notifications_for_farm(*, farm: FarmHub, since_id=None) -> QuerySet[FarmNotification]:
    try:
        queryset = FarmNotification.objects.filter(farm=farm)
        if since_id is not None:
            queryset = queryset.filter(id__gt=since_id)
        return queryset.order_by("created_at", "id")
    except (ProgrammingError, OperationalError) as exc:
        raise ValueError("Notifications table is not migrated.") from exc


def get_prioritized_notifications_for_farm(*, farm: FarmHub, since_id=None, limit=5) -> QuerySet[FarmNotification]:
    try:
        unread_queryset = get_notifications_for_farm(farm=farm, since_id=since_id).filter(is_read=False)
        unread_count = unread_queryset.count()

        if unread_count >= limit:
            return unread_queryset[:limit]

        fallback_limit = max(limit - unread_count, 0)
        if fallback_limit == 0:
            return unread_queryset

        queryset = get_notifications_for_farm(farm=farm, since_id=since_id).annotate(
            priority=Case(
                When(is_read=False, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        )
        return queryset.order_by("priority", "created_at", "id")[:limit]
    except (ProgrammingError, OperationalError) as exc:
        raise ValueError("Notifications table is not migrated.") from exc


def mark_notifications_as_read(*, farm: FarmHub, slice_id: int) -> int:
    try:
        return FarmNotification.objects.filter(
            farm=farm,
            id__lte=slice_id,
            is_read=False,
        ).update(is_read=True)
    except (ProgrammingError, OperationalError) as exc:
        raise ValueError("Notifications table is not migrated.") from exc


def long_poll_notifications(*, farm: FarmHub, since_id=None, timeout_seconds=DEFAULT_POLL_TIMEOUT_SECONDS, interval_seconds=DEFAULT_POLL_INTERVAL_SECONDS, limit=5):
    deadline = time.monotonic() + max(timeout_seconds, 0)
    while True:
        notifications = list(get_prioritized_notifications_for_farm(farm=farm, since_id=since_id, limit=limit))
        if notifications:
            return notifications
        if time.monotonic() >= deadline:
            return []
        time.sleep(max(interval_seconds, 0))
