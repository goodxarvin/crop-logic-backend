from django.db import ProgrammingError, OperationalError

from notifications.services import create_notification_for_farm_uuid


DEFAULT_SENSOR_EXTERNAL_FARM_UUID = "11111111-1111-1111-1111-111111111111"


def create_sensor_external_notification(*, payload=None):
    payload = payload or {}
    try:
        return create_notification_for_farm_uuid(
            farm_uuid=DEFAULT_SENSOR_EXTERNAL_FARM_UUID,
            title="Sensor external API request",
            message="A request was received by sensor_external_api.",
            level="info",
            metadata={"payload": payload},
        )
    except (ProgrammingError, OperationalError) as exc:
        raise ValueError("Notifications table is not migrated.") from exc
