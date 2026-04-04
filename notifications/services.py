import time

from django.db import OperationalError, ProgrammingError
from django.db.models import QuerySet

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


def long_poll_notifications(*, farm: FarmHub, since_id=None, timeout_seconds=DEFAULT_POLL_TIMEOUT_SECONDS, interval_seconds=DEFAULT_POLL_INTERVAL_SECONDS):
    deadline = time.monotonic() + max(timeout_seconds, 0)
    while True:
        notifications = list(get_notifications_for_farm(farm=farm, since_id=since_id))
        if notifications:
            return notifications
        if time.monotonic() >= deadline:
            return []
        time.sleep(max(interval_seconds, 0))
