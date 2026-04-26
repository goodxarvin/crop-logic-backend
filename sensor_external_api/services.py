from django.conf import settings
from django.db import OperationalError, ProgrammingError, transaction

from external_api_adapter import request as external_api_request
from external_api_adapter.exceptions import ExternalAPIRequestError
from farm_hub.models import FarmSensor
from notifications.services import create_notification_for_farm_uuid

from .models import SensorExternalRequestLog


class FarmDataForwardError(Exception):
    pass


def get_sensor_external_request_logs_for_farm(*, farm_uuid):
    try:
        return SensorExternalRequestLog.objects.filter(farm_uuid=farm_uuid).order_by("-created_at", "-id")
    except (ProgrammingError, OperationalError) as exc:
        raise ValueError("Sensor external API tables are not migrated.") from exc


def get_farm_sensor_map_for_logs(*, logs):
    try:
        logs = list(logs)
        if not logs:
            return {}

        farm_sensor_queryset = (
            FarmSensor.objects.select_related("farm", "sensor_catalog")
            .filter(
                farm__farm_uuid__in={log.farm_uuid for log in logs},
                physical_device_uuid__in={log.physical_device_uuid for log in logs},
            )
            .order_by("-created_at", "-id")
        )

        farm_sensor_map = {}
        for farm_sensor in farm_sensor_queryset:
            key = (
                farm_sensor.farm.farm_uuid,
                farm_sensor.sensor_catalog.uuid if farm_sensor.sensor_catalog else None,
                farm_sensor.physical_device_uuid,
            )
            farm_sensor_map.setdefault(key, farm_sensor)

        return farm_sensor_map
    except (ProgrammingError, OperationalError) as exc:
        raise ValueError("Sensor external API tables are not migrated.") from exc


def get_latest_sensor_external_request_log(*, farm_uuid, sensor_catalog_uuid, physical_device_uuid):
    try:
        return (
            SensorExternalRequestLog.objects.filter(
                farm_uuid=farm_uuid,
                sensor_catalog_uuid=sensor_catalog_uuid,
                physical_device_uuid=physical_device_uuid,
            )
            .order_by("-created_at", "-id")
            .first()
        )
    except (ProgrammingError, OperationalError) as exc:
        raise ValueError("Sensor external API tables are not migrated.") from exc


def create_sensor_external_notification(*, physical_device_uuid, payload=None):
    payload = payload or {}
    sensor = (
        FarmSensor.objects.select_related("farm", "farm__current_crop_area", "sensor_catalog")
        .filter(physical_device_uuid=physical_device_uuid)
        .first()
    )
    if sensor is None:
        raise ValueError("Physical device not found.")

    try:
        with transaction.atomic():
            SensorExternalRequestLog.objects.create(
                farm_uuid=sensor.farm.farm_uuid,
                sensor_catalog_uuid=sensor.sensor_catalog.uuid if sensor.sensor_catalog else None,
                physical_device_uuid=sensor.physical_device_uuid,
                payload=payload,
            )
            return create_notification_for_farm_uuid(
                farm_uuid=sensor.farm.farm_uuid,
                title="Sensor external API request",
                message=f"Payload received from device {sensor.physical_device_uuid}.",
                level="info",
                metadata={
                    "farm_uuid": str(sensor.farm.farm_uuid),
                    "sensor_catalog_uuid": str(sensor.sensor_catalog.uuid) if sensor.sensor_catalog else None,
                    "physical_device_uuid": str(sensor.physical_device_uuid),
                    "payload": payload,
                },
            )
    except (ProgrammingError, OperationalError) as exc:
        raise ValueError("Sensor external API tables are not migrated.") from exc


def forward_sensor_payload_to_farm_data(*, physical_device_uuid, payload=None):
    payload = payload or {}
    sensor = (
        FarmSensor.objects.select_related("farm", "farm__current_crop_area")
        .filter(physical_device_uuid=physical_device_uuid)
        .first()
    )
    if sensor is None:
        raise ValueError("Physical device not found.")

    farm_boundary = _get_farm_boundary(sensor=sensor)
    api_key = getattr(settings, "FARM_DATA_API_KEY", "")
    if not api_key:
        raise FarmDataForwardError("FARM_DATA_API_KEY is not configured.")

    request_payload = {
        "farm_uuid": str(sensor.farm.farm_uuid),
        "farm_boundary": farm_boundary,
        "sensor_payload": {
            sensor.name or str(sensor.physical_device_uuid): payload,
        },
    }

    try:
        response = external_api_request(
            "ai",
            _get_farm_data_path(),
            method="POST",
            payload=request_payload,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-API-Key": api_key,
                "Authorization": f"Api-Key {api_key}",
            },
        )
    except ExternalAPIRequestError as exc:
        raise FarmDataForwardError(f"Farm data API request failed: {exc}") from exc

    if response.status_code >= 400:
        response_body = response.data
        raise FarmDataForwardError(
            f"Farm data API returned status {response.status_code}: {response_body}"
        )

    return request_payload


def _get_farm_boundary(*, sensor):
    crop_area = sensor.farm.current_crop_area or sensor.farm.crop_areas.order_by("-created_at", "-id").first()
    if crop_area is None:
        raise FarmDataForwardError("Farm boundary is not configured for this farm.")

    geometry = crop_area.geometry or {}
    if geometry.get("type") == "Feature":
        geometry = geometry.get("geometry") or {}

    if geometry.get("type") != "Polygon":
        raise FarmDataForwardError("Farm boundary geometry must be a Polygon.")

    return geometry


def _get_farm_data_path():
    return getattr(settings, "FARM_DATA_API_PATH", "/api/farm-data/")
