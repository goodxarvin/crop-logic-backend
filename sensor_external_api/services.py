import logging

from django.conf import settings
from django.db import OperationalError, ProgrammingError, transaction

from external_api_adapter import request as external_api_request
from external_api_adapter.exceptions import ExternalAPIRequestError
from farm_hub.models import FarmSensor
from notifications.services import create_notification_for_farm_uuid

from .models import SensorExternalRequestLog


logger = logging.getLogger(__name__)


class FarmDataForwardError(Exception):
    pass


def get_sensor_external_request_logs_for_farm(
    *,
    farm_uuid,
    physical_device_uuid=None,
    sensor_type=None,
    date_from=None,
    date_to=None,
):
    try:
        queryset = SensorExternalRequestLog.objects.filter(farm_uuid=farm_uuid)

        if physical_device_uuid:
            queryset = queryset.filter(physical_device_uuid=physical_device_uuid)

        if sensor_type:
            physical_device_uuids = FarmSensor.objects.filter(
                farm__farm_uuid=farm_uuid,
                sensor_type=sensor_type,
            ).values_list("physical_device_uuid", flat=True)
            queryset = queryset.filter(physical_device_uuid__in=physical_device_uuids)

        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)

        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        return queryset.order_by("-created_at", "-id")
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
            exact_key = (
                farm_sensor.farm.farm_uuid,
                farm_sensor.sensor_catalog.uuid if farm_sensor.sensor_catalog else None,
                farm_sensor.physical_device_uuid,
            )
            fallback_key = (
                farm_sensor.farm.farm_uuid,
                None,
                farm_sensor.physical_device_uuid,
            )
            farm_sensor_map.setdefault(exact_key, farm_sensor)
            farm_sensor_map.setdefault(fallback_key, farm_sensor)

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
    logger.warning(
        "Sensor external notification start: physical_device_uuid=%s payload_type=%s payload_keys=%s",
        physical_device_uuid,
        type(payload).__name__,
        sorted(payload.keys()) if isinstance(payload, dict) else None,
    )
    sensor = (
        FarmSensor.objects.select_related("farm", "farm__current_crop_area", "sensor_catalog")
        .filter(physical_device_uuid=physical_device_uuid)
        .first()
    )
    if sensor is None:
        logger.error(
            "Sensor external notification failed: physical device not found for uuid=%s",
            physical_device_uuid,
        )
        raise ValueError("Physical device not found.")

    try:
        with transaction.atomic():
            SensorExternalRequestLog.objects.create(
                farm_uuid=sensor.farm.farm_uuid,
                sensor_catalog_uuid=sensor.sensor_catalog.uuid if sensor.sensor_catalog else None,
                physical_device_uuid=sensor.physical_device_uuid,
                payload=payload,
            )
            notification = create_notification_for_farm_uuid(
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
            logger.warning(
                "Sensor external notification created: farm_uuid=%s sensor_catalog_uuid=%s physical_device_uuid=%s",
                sensor.farm.farm_uuid,
                sensor.sensor_catalog.uuid if sensor.sensor_catalog else None,
                sensor.physical_device_uuid,
            )
            return notification
    except (ProgrammingError, OperationalError) as exc:
        logger.exception(
            "Sensor external notification failed due to database readiness: physical_device_uuid=%s",
            physical_device_uuid,
        )
        raise ValueError("Sensor external API tables are not migrated.") from exc


def forward_sensor_payload_to_farm_data(*, physical_device_uuid, payload=None):
    payload = payload or {}
    sensor = (
        FarmSensor.objects.select_related("farm", "farm__current_crop_area", "sensor_catalog")
        .filter(physical_device_uuid=physical_device_uuid)
        .first()
    )
    if sensor is None:
        logger.error(
            "Farm data forward failed: physical device not found for uuid=%s",
            physical_device_uuid,
        )
        raise ValueError("Physical device not found.")

    farm_boundary = _get_farm_boundary(sensor=sensor)
    api_key = getattr(settings, "FARM_DATA_API_KEY", "")
    if not api_key:
        logger.error(
            "Farm data forward failed: FARM_DATA_API_KEY missing for farm_uuid=%s physical_device_uuid=%s",
            sensor.farm.farm_uuid,
            physical_device_uuid,
        )
        raise FarmDataForwardError("FARM_DATA_API_KEY is not configured.")

    sensor_key = _get_sensor_key(sensor=sensor)
    normalized_sensor_payload = _normalize_sensor_payload(sensor_key=sensor_key, sensor_payload=payload)
    request_payload = {
        "farm_uuid": str(sensor.farm.farm_uuid),
        "farm_boundary": farm_boundary,
        "sensor_key": sensor_key,
        "sensor_payload": normalized_sensor_payload,
    }
    logger.warning(
        "Farm data forward start: farm_uuid=%s physical_device_uuid=%s sensor_key=%s payload_keys=%s boundary_type=%s boundary_points=%s",
        sensor.farm.farm_uuid,
        physical_device_uuid,
        sensor_key,
        sorted(normalized_sensor_payload.keys()) if isinstance(normalized_sensor_payload, dict) else None,
        farm_boundary.get("type") if isinstance(farm_boundary, dict) else None,
        len(farm_boundary.get("coordinates", [[]])[0]) if isinstance(farm_boundary, dict) and farm_boundary.get("coordinates") else None,
    )

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
        logger.exception(
            "Farm data forward request exception: farm_uuid=%s physical_device_uuid=%s sensor_key=%s",
            sensor.farm.farm_uuid,
            physical_device_uuid,
            sensor_key,
        )
        raise FarmDataForwardError(f"Farm data API request failed: {exc}") from exc

    if response.status_code >= 400:
        response_body = response.data
        logger.error(
            "Farm data forward rejected: farm_uuid=%s physical_device_uuid=%s sensor_key=%s status_code=%s response=%s",
            sensor.farm.farm_uuid,
            physical_device_uuid,
            sensor_key,
            response.status_code,
            response_body,
        )
        raise FarmDataForwardError(
            f"Farm data API returned status {response.status_code}: {response_body}"
        )

    logger.warning(
        "Farm data forward success: farm_uuid=%s physical_device_uuid=%s sensor_key=%s status_code=%s",
        sensor.farm.farm_uuid,
        physical_device_uuid,
        sensor_key,
        response.status_code,
    )
    return request_payload


def _get_farm_boundary(*, sensor):
    crop_area = sensor.farm.current_crop_area or sensor.farm.crop_areas.order_by("-created_at", "-id").first()
    if crop_area is None:
        logger.error(
            "Farm data forward failed: no farm boundary configured for farm_uuid=%s physical_device_uuid=%s",
            sensor.farm.farm_uuid,
            sensor.physical_device_uuid,
        )
        raise FarmDataForwardError("Farm boundary is not configured for this farm.")

    geometry = crop_area.geometry or {}
    if geometry.get("type") == "Feature":
        geometry = geometry.get("geometry") or {}

    if geometry.get("type") != "Polygon":
        logger.error(
            "Farm data forward failed: invalid boundary geometry type=%s for farm_uuid=%s physical_device_uuid=%s",
            geometry.get("type"),
            sensor.farm.farm_uuid,
            sensor.physical_device_uuid,
        )
        raise FarmDataForwardError("Farm boundary geometry must be a Polygon.")

    return geometry


def _normalize_sensor_payload(*, sensor_key, sensor_payload):
    if not sensor_payload:
        return {}
    if not isinstance(sensor_payload, dict):
        raise FarmDataForwardError("`payload` must be a JSON object.")

    if all(isinstance(value, dict) for value in sensor_payload.values()):
        return sensor_payload
    return {sensor_key: sensor_payload}


def _get_sensor_key(*, sensor):
    if sensor.sensor_catalog and sensor.sensor_catalog.code:
        return sensor.sensor_catalog.code
    return "sensor-7-1"


def _get_farm_data_path():
    return getattr(settings, "FARM_DATA_API_PATH", "/api/farm-data/")
