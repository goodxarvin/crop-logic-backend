from copy import deepcopy
from datetime import timedelta
import logging
import uuid

from django.conf import settings
from django.db import OperationalError, ProgrammingError, transaction
from django.utils import timezone

from config.failure_contract import StructuredServiceError
from external_api_adapter import request as external_api_request
from external_api_adapter.exceptions import ExternalAPIRequestError
from notifications.services import create_notification_for_farm_uuid

from .models import FarmDevice, SensorExternalRequestLog
from .templates import AVG_SOIL_MOISTURE_TEMPLATE, SENSOR_META_TEMPLATE, SOIL_MOISTURE_HEATMAP_TEMPLATE

logger = logging.getLogger(__name__)


class FarmDataForwardError(Exception):
    pass


class DeviceDataUnavailableError(StructuredServiceError):
    def __init__(self, *, error_code: str, message: str, details: dict | None = None, retriable: bool = False):
        super().__init__(
            error_code=error_code,
            message=message,
            source="db",
            details=details,
            retriable=retriable,
        )

SENSOR_FIELDS = [
    {"id": "soil_moisture", "label": "رطوبت خاک", "unit": "%", "payload_keys": ("soil_moisture", "soilMoisture", "moisture"), "ideal_min": 45.0, "ideal_max": 65.0, "radar_label": "رطوبت"},
    {"id": "soil_temperature", "label": "دمای خاک", "unit": "°C", "payload_keys": ("soil_temperature", "soilTemperature", "temperature"), "ideal_min": 18.0, "ideal_max": 28.0, "radar_label": "دما"},
    {"id": "soil_ph", "label": "pH خاک", "unit": "pH", "payload_keys": ("soil_ph", "soilPh", "ph"), "ideal_min": 6.0, "ideal_max": 7.5, "radar_label": "pH"},
    {"id": "electrical_conductivity", "label": "هدایت الکتریکی", "unit": "dS/m", "payload_keys": ("electrical_conductivity", "electricalConductivity", "ec"), "ideal_min": 0.8, "ideal_max": 1.8, "radar_label": "EC"},
    {"id": "nitrogen", "label": "نیتروژن", "unit": "mg/kg", "payload_keys": ("nitrogen", "n"), "ideal_min": 20.0, "ideal_max": 40.0, "radar_label": "نیتروژن"},
    {"id": "phosphorus", "label": "فسفر", "unit": "mg/kg", "payload_keys": ("phosphorus", "p"), "ideal_min": 10.0, "ideal_max": 25.0, "radar_label": "فسفر"},
    {"id": "potassium", "label": "پتاسیم", "unit": "mg/kg", "payload_keys": ("potassium", "k"), "ideal_min": 15.0, "ideal_max": 35.0, "radar_label": "پتاسیم"},
]
MAX_HISTORY_ITEMS = 20
MAX_CHART_POINTS = 7
COMPARISON_CHART_RANGES = {"7d": 7, "30d": 30}
VALUES_LIST_RANGES = {"1h": timedelta(hours=1), "24h": timedelta(hours=24), "7d": timedelta(days=7)}
RADAR_CHART_RANGES = {"today": timedelta(days=1), "7d": timedelta(days=7), "30d": timedelta(days=30)}
PERSIAN_WEEKDAYS = {0: "دوشنبه", 1: "سه شنبه", 2: "چهارشنبه", 3: "پنج شنبه", 4: "جمعه", 5: "شنبه", 6: "یکشنبه"}
COMPARISON_CHART_FIELD_ALIASES = {"soil_moisture": "moisture", "soilMoisture": "moisture", "moisture": "moisture", "soil_temperature": "temperature", "soilTemperature": "temperature", "temperature": "temperature", "humidity": "humidity", "soil_ph": "ph", "soilPh": "ph", "ph": "ph", "electrical_conductivity": "ec", "electricalConductivity": "ec", "ec": "ec", "nitrogen": "nitrogen", "n": "nitrogen", "phosphorus": "phosphorus", "p": "phosphorus", "potassium": "potassium", "k": "potassium"}
COMPARISON_CHART_PRIMARY_FIELDS = ("moisture", "temperature", "humidity", "ph", "ec", "nitrogen", "phosphorus", "potassium")
VALUES_LIST_FIELDS = [("moisture", "Moisture", "%"), ("temperature", "Temperature", "°C"), ("humidity", "Humidity", "%"), ("ph", "pH", "pH"), ("ec", "EC", "dS/m"), ("nitrogen", "Nitrogen", "mg/kg"), ("phosphorus", "Phosphorus", "mg/kg"), ("potassium", "Potassium", "mg/kg")]
RADAR_CHART_FIELDS = [("moisture", "Moisture", 60.0), ("temperature", "Temperature", 26.0), ("humidity", "Humidity", 55.0), ("ph", "PH", 6.5), ("ec", "EC", 1.3), ("nitrogen", "Nitrogen", 42.0), ("potassium", "Potassium", 38.0)]


def get_sensor_external_request_logs_for_farm(*, farm_uuid, physical_device_uuid=None, sensor_type=None, date_from=None, date_to=None):
    try:
        queryset = SensorExternalRequestLog.objects.filter(farm_uuid=farm_uuid)
        if physical_device_uuid:
            queryset = queryset.filter(physical_device_uuid=physical_device_uuid)
        if sensor_type:
            physical_device_uuids = FarmDevice.objects.filter(farm__farm_uuid=farm_uuid, sensor_type=sensor_type).values_list("physical_device_uuid", flat=True)
            queryset = queryset.filter(physical_device_uuid__in=physical_device_uuids)
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        return queryset.order_by("-created_at", "-id")
    except (ProgrammingError, OperationalError) as exc:
        raise ValueError("Sensor external API tables are not migrated.") from exc


def get_farm_device_map_for_logs(*, logs):
    try:
        logs = list(logs)
        if not logs:
            return {}
        farm_device_queryset = FarmDevice.objects.select_related("farm", "sensor_catalog").filter(
            farm__farm_uuid__in={log.farm_uuid for log in logs},
            physical_device_uuid__in={log.physical_device_uuid for log in logs},
        ).order_by("-created_at", "-id")
        farm_device_map = {}
        for farm_device in farm_device_queryset:
            exact_key = (farm_device.farm.farm_uuid, farm_device.sensor_catalog.uuid if farm_device.sensor_catalog else None, farm_device.physical_device_uuid)
            fallback_key = (farm_device.farm.farm_uuid, None, farm_device.physical_device_uuid)
            farm_device_map.setdefault(exact_key, farm_device)
            farm_device_map.setdefault(fallback_key, farm_device)
        return farm_device_map
    except (ProgrammingError, OperationalError) as exc:
        raise ValueError("Sensor external API tables are not migrated.") from exc


def get_latest_sensor_external_request_log(*, farm_uuid, sensor_catalog_uuid, physical_device_uuid):
    try:
        return SensorExternalRequestLog.objects.filter(farm_uuid=farm_uuid, sensor_catalog_uuid=sensor_catalog_uuid, physical_device_uuid=physical_device_uuid).order_by("-created_at", "-id").first()
    except (ProgrammingError, OperationalError) as exc:
        raise ValueError("Sensor external API tables are not migrated.") from exc


def create_sensor_external_notification(*, physical_device_uuid, payload=None):
    payload = payload or {}
    sensor = FarmDevice.objects.select_related("farm", "farm__current_crop_area", "sensor_catalog").filter(physical_device_uuid=physical_device_uuid).first()
    runtime_context = build_sensor_runtime_context(sensor=sensor, payload=payload)
    return create_sensor_external_notification_for_sensor(sensor=sensor, payload=payload, runtime_context=runtime_context)


def create_sensor_external_notification_for_sensor(*, sensor, payload=None, runtime_context=None):
    payload = payload or {}
    if sensor is None:
        raise ValueError("Physical device not found.")
    runtime_context = runtime_context or build_sensor_runtime_context(sensor=sensor, payload=payload)
    try:
        with transaction.atomic():
            SensorExternalRequestLog.objects.create(
                farm_uuid=sensor.farm.farm_uuid,
                sensor_catalog_uuid=sensor.sensor_catalog.uuid if sensor.sensor_catalog else None,
                physical_device_uuid=sensor.physical_device_uuid,
                cluster_uuid=runtime_context["cluster_uuid"],
                location_metadata=runtime_context["location_metadata"],
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
                    "cluster_uuid": str(runtime_context["cluster_uuid"]) if runtime_context["cluster_uuid"] else None,
                    "location_metadata": runtime_context["location_metadata"],
                    "payload": payload,
                },
            )
    except (ProgrammingError, OperationalError) as exc:
        raise ValueError("Sensor external API tables are not migrated.") from exc


def forward_sensor_payload_to_farm_data(*, physical_device_uuid, payload=None):
    payload = payload or {}
    sensor = FarmDevice.objects.select_related("farm", "farm__current_crop_area", "sensor_catalog").filter(physical_device_uuid=physical_device_uuid).first()
    runtime_context = build_sensor_runtime_context(sensor=sensor, payload=payload)
    return forward_sensor_payload_to_farm_data_for_sensor(sensor=sensor, payload=payload, runtime_context=runtime_context)


def forward_sensor_payload_to_farm_data_for_sensor(*, sensor, payload=None, runtime_context=None):
    payload = payload or {}
    if sensor is None:
        raise ValueError("Physical device not found.")
    farm_boundary = _get_farm_boundary(sensor=sensor)
    api_key = getattr(settings, "FARM_DATA_API_KEY", "")
    if not api_key:
        raise FarmDataForwardError("FARM_DATA_API_KEY is not configured.")
    runtime_context = runtime_context or build_sensor_runtime_context(sensor=sensor, payload=payload)
    sensor_key = _get_sensor_key(sensor=sensor)
    request_payload = {
        "farm_uuid": str(sensor.farm.farm_uuid),
        "farm_boundary": farm_boundary,
        "sensor_key": sensor_key,
        "sensor_payload": _build_ai_sensor_payload(
            sensor=sensor,
            sensor_key=sensor_key,
            sensor_payload=payload,
            runtime_context=runtime_context,
        ),
    }
    try:
        response = external_api_request(
            "ai",
            _get_farm_data_path(),
            method="POST",
            payload=request_payload,
            headers={"Accept": "application/json", "Content-Type": "application/json", "X-API-Key": api_key, "Authorization": f"Api-Key {api_key}"},
        )
    except ExternalAPIRequestError as exc:
        raise FarmDataForwardError(f"Farm data API request failed: {exc}") from exc
    if response.status_code >= 400:
        raise FarmDataForwardError(f"Farm data API returned status {response.status_code}: {response.data}")
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


def _normalize_sensor_payload(*, sensor_key, sensor_payload):
    if not sensor_payload:
        return {}
    if not isinstance(sensor_payload, dict):
        raise FarmDataForwardError("`payload` must be a JSON object.")
    if all(isinstance(value, dict) for value in sensor_payload.values()):
        return sensor_payload
    return {sensor_key: sensor_payload}


def _build_ai_sensor_payload(*, sensor, sensor_key, sensor_payload, runtime_context=None):
    if sensor_payload and not isinstance(sensor_payload, dict):
        raise FarmDataForwardError("`payload` must be a JSON object.")
    raw_payload = _extract_payload(sensor_payload)
    runtime_context = runtime_context or build_sensor_runtime_context(sensor=sensor, payload=sensor_payload)

    device_payload = {
        "sensor_key": sensor_key,
        "physical_device_uuid": str(sensor.physical_device_uuid),
        "recorded_at": timezone.now().isoformat(),
        "metrics": raw_payload or {},
        "metadata": {
            "source_service": "backend_device_hub",
            "farm_device_uuid": str(sensor.uuid),
            "sensor_catalog_uuid": str(sensor.sensor_catalog.uuid) if sensor.sensor_catalog else None,
            "sensor_type": sensor.sensor_type or "",
            "device_name": sensor.name or "",
            "cluster_uuid": str(runtime_context["cluster_uuid"]) if runtime_context["cluster_uuid"] else None,
            "location": runtime_context["location_metadata"],
        },
    }
    if runtime_context["cluster_uuid"] is not None:
        device_payload["cluster_uuid"] = str(runtime_context["cluster_uuid"])
    if runtime_context["location_metadata"].get("zone") is not None:
        device_payload["zone"] = runtime_context["location_metadata"]["zone"]
    if runtime_context["location_metadata"].get("depth_cm") is not None:
        device_payload["depth_cm"] = runtime_context["location_metadata"]["depth_cm"]

    return {
        sensor.get_ai_device_key(): device_payload
    }


def build_sensor_runtime_context(*, sensor, payload=None):
    payload = payload or {}
    payload_location = _extract_payload_location_metadata(payload)
    payload_cluster_uuid = _extract_cluster_uuid(payload)

    location_metadata = dict(sensor.location_metadata or {})
    location_metadata.update(payload_location)

    return {
        "cluster_uuid": payload_cluster_uuid or sensor.cluster_uuid,
        "location_metadata": location_metadata,
    }


def sync_sensor_runtime_context(*, sensor, payload=None):
    if sensor is None:
        raise ValueError("Physical device not found.")

    runtime_context = build_sensor_runtime_context(sensor=sensor, payload=payload)
    update_fields = []
    if runtime_context["cluster_uuid"] != sensor.cluster_uuid:
        sensor.cluster_uuid = runtime_context["cluster_uuid"]
        update_fields.append("cluster_uuid")
    if runtime_context["location_metadata"] != (sensor.location_metadata or {}):
        sensor.location_metadata = runtime_context["location_metadata"]
        update_fields.append("location_metadata")
    if update_fields:
        update_fields.append("updated_at")
        sensor.save(update_fields=update_fields)
    return runtime_context


def _extract_cluster_uuid(payload):
    if not isinstance(payload, dict):
        return None
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    candidates = [
        payload.get("cluster_uuid"),
        payload.get("clusterId"),
        metadata.get("cluster_uuid"),
        metadata.get("clusterId"),
    ]
    for candidate in candidates:
        parsed = _parse_uuid(candidate)
        if parsed is not None:
            return parsed
    return None


def _extract_payload_location_metadata(payload):
    if not isinstance(payload, dict):
        return {}

    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    location = payload.get("location") if isinstance(payload.get("location"), dict) else {}
    coordinates = payload.get("coordinates") if isinstance(payload.get("coordinates"), dict) else {}

    lat = payload.get("lat", payload.get("latitude"))
    lon = payload.get("lon", payload.get("lng", payload.get("longitude")))
    if lat is None:
        lat = location.get("lat", location.get("latitude"))
    if lon is None:
        lon = location.get("lon", location.get("lng", location.get("longitude")))
    if lat is None:
        lat = coordinates.get("lat", coordinates.get("latitude"))
    if lon is None:
        lon = coordinates.get("lon", coordinates.get("lng", coordinates.get("longitude")))

    result = {}
    if lat is not None:
        result["lat"] = lat
    if lon is not None:
        result["lon"] = lon

    for key in ("zone", "depth_cm", "cluster_code", "cluster_label"):
        value = payload.get(key, metadata.get(key))
        if value not in (None, ""):
            result[key] = value

    if location:
        result["location"] = location
    elif coordinates:
        result["location"] = coordinates

    return result


def _parse_uuid(value):
    if value in (None, ""):
        return None
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError, AttributeError):
        return None


def _get_sensor_key(*, sensor):
    return sensor.get_sensor_key()


def _get_farm_data_path():
    return getattr(settings, "FARM_DATA_API_PATH", "/api/farm-data/")


def _to_float(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_payload(payload):
    if not isinstance(payload, dict):
        return {}
    if isinstance(payload.get("payload"), dict):
        payload = payload["payload"]
    if isinstance(payload.get("data"), dict):
        nested = payload["data"]
        if any(any(key in nested for key in field["payload_keys"]) for field in SENSOR_FIELDS):
            payload = nested
    return payload


def _extract_numeric_payload(payload):
    payload = _extract_payload(payload)
    return {key: numeric_value for key, value in payload.items() if (numeric_value := _to_float(value)) is not None}


def _extract_readings(payload):
    payload = _extract_payload(payload)
    readings = {}
    for field in SENSOR_FIELDS:
        for key in field["payload_keys"]:
            value = _to_float(payload.get(key))
            if value is not None:
                readings[field["id"]] = value
                break
    return readings


def _format_number(value):
    if value is None:
        return ""
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.1f}".rstrip("0").rstrip(".")


def _format_value(value, unit):
    number = _format_number(value)
    if not number:
        return number
    if unit in {"", "pH"}:
        return number
    if unit in {"%", "°C"}:
        return f"{number}{unit}"
    return f"{number} {unit}"


def _format_range(field):
    lower = _format_number(field["ideal_min"])
    upper = _format_number(field["ideal_max"])
    if field["unit"] in {"", "pH"}:
        return f"{lower}-{upper}"
    return f"{lower}-{upper} {field['unit']}"


def get_primary_soil_sensor(*, farm):
    soil_sensors = list(farm.sensors.select_related("sensor_catalog").order_by("created_at", "id"))

    def _sensor_priority(sensor):
        sensor_type = (sensor.sensor_type or "").lower()
        catalog_code = (sensor.sensor_catalog.code if sensor.sensor_catalog else "").lower()
        catalog_name = (sensor.sensor_catalog.name if sensor.sensor_catalog else "").lower()
        sensor_name = (sensor.name or "").lower()
        haystack = " ".join([sensor_type, catalog_code, catalog_name, sensor_name])
        if "sensor-7-in-1" in catalog_code or "soil_7_in_1" in sensor_type:
            return 0
        if "7 in 1" in haystack or "7-in-1" in haystack or "7in1" in haystack:
            return 1
        if "soil" in haystack:
            return 2
        return 3

    prioritized_sensors = sorted(soil_sensors, key=_sensor_priority)
    if prioritized_sensors and _sensor_priority(prioritized_sensors[0]) < 3:
        return prioritized_sensors[0]
    return soil_sensors[0] if soil_sensors else None


def _get_sensor_context(farm=None):
    if farm is None:
        raise DeviceDataUnavailableError(
            error_code="missing_farm",
            message="Farm instance is required for sensor context lookup.",
        )
    primary_sensor = get_primary_soil_sensor(farm=farm)
    if primary_sensor is None:
        raise DeviceDataUnavailableError(
            error_code="sensor_not_found",
            message=f"No primary soil sensor found for farm_uuid={farm.farm_uuid}.",
            details={"farm_uuid": str(farm.farm_uuid)},
        )
    try:
        logs_queryset = get_sensor_external_request_logs_for_farm(farm_uuid=farm.farm_uuid, physical_device_uuid=primary_sensor.physical_device_uuid)
    except ValueError as exc:
        raise DeviceDataUnavailableError(
            error_code="history_unavailable",
            message=f"Sensor history lookup failed for farm_uuid={farm.farm_uuid}.",
            details={"farm_uuid": str(farm.farm_uuid)},
            retriable=True,
        ) from exc
    history = []
    for log in logs_queryset[:MAX_HISTORY_ITEMS]:
        readings = _extract_readings(log.payload)
        if readings:
            history.append((log, readings))
    if not history:
        raise DeviceDataUnavailableError(
            error_code="no_sensor_readings",
            message=f"No sensor readings found for farm_uuid={farm.farm_uuid}.",
            details={"farm_uuid": str(farm.farm_uuid)},
        )
    latest_log, latest_readings = history[0]
    farm_device_map = get_farm_device_map_for_logs(logs=[latest_log])
    farm_device = farm_device_map.get((latest_log.farm_uuid, latest_log.sensor_catalog_uuid, latest_log.physical_device_uuid)) or primary_sensor
    return {"farm_device": farm_device, "latest_log": latest_log, "latest_readings": latest_readings, "previous_readings": history[1][1] if len(history) > 1 else {}, "history": history}


def _build_sensor_meta(context, fallback_sensor):
    sensor = deepcopy(fallback_sensor)
    if not context:
        return sensor
    farm_device = context.get("farm_device")
    latest_log = context["latest_log"]
    sensor["physicalDeviceUuid"] = str(latest_log.physical_device_uuid)
    sensor["updatedAt"] = latest_log.created_at.isoformat()
    if farm_device is not None:
        sensor["name"] = farm_device.name or sensor["name"]
        if farm_device.sensor_catalog is not None:
            sensor["sensorCatalogCode"] = farm_device.sensor_catalog.code
    return sensor


def _calculate_status_chip(value):
    if value is None:
        return ("نامشخص", "secondary", "secondary")
    if value >= 60:
        return ("بهینه", "success", "primary")
    if value >= 45:
        return ("متوسط", "warning", "warning")
    return ("کم", "error", "error")


def get_sensor_7_in_1_values_list_data(farm=None, context=None):
    context = _get_sensor_context(farm) if context is None else context
    data = {
        "sensor": _build_sensor_meta(context, SENSOR_META_TEMPLATE),
        "sensors": [],
    }
    latest_readings = context["latest_readings"]
    previous_readings = context["previous_readings"]
    for field in SENSOR_FIELDS:
        value = latest_readings.get(field["id"])
        if value is None:
            continue
        previous = previous_readings.get(field["id"])
        change = 0.0 if previous is None else round(value - previous, 2)
        data["sensors"].append({"id": field["id"], "title": _format_value(value, field["unit"]), "subtitle": field["label"], "trendNumber": abs(change), "trend": "positive" if change >= 0 else "negative", "unit": field["unit"]})
    if not data["sensors"]:
        raise DeviceDataUnavailableError(
            error_code="no_numeric_readings",
            message=f"Latest sensor payload has no usable numeric values for farm_uuid={farm.farm_uuid if farm else None}.",
        )
    return data


def get_sensor_7_in_1_avg_soil_moisture_data(farm=None, context=None):
    context = _get_sensor_context(farm) if context is None else context
    moisture = context["latest_readings"].get("soil_moisture")
    if moisture is None:
        raise DeviceDataUnavailableError(
            error_code="missing_soil_moisture",
            message=f"Latest sensor payload is missing soil_moisture for farm_uuid={farm.farm_uuid if farm else None}.",
        )
    chip_text, chip_color, avatar_color = _calculate_status_chip(moisture)
    return {
        **deepcopy(AVG_SOIL_MOISTURE_TEMPLATE),
        "stats": _format_value(moisture, "%"),
        "chipText": chip_text,
        "chipColor": chip_color,
        "avatarColor": avatar_color,
        "status": "success",
        "source": "db",
    }


def _score_field(value, field):
    min_value = field["ideal_min"]
    max_value = field["ideal_max"]
    midpoint = (min_value + max_value) / 2
    half_span = max((max_value - min_value) / 2, 0.1)
    distance = abs(value - midpoint)
    if min_value <= value <= max_value:
        return round(max(80.0, 100.0 - ((distance / half_span) * 20.0)), 1)
    overflow = max(0.0, distance - half_span)
    return round(max(0.0, 80.0 - ((overflow / half_span) * 80.0)), 1)


def get_sensor_7_in_1_radar_chart_data(farm=None, context=None):
    context = _get_sensor_context(farm) if context is None else context
    latest_readings = context["latest_readings"]
    scores, labels = [], []
    for field in SENSOR_FIELDS:
        value = latest_readings.get(field["id"])
        if value is None:
            continue
        labels.append(field["radar_label"])
        scores.append(_score_field(value, field))
    if not labels:
        raise DeviceDataUnavailableError(
            error_code="no_radar_data",
            message=f"No usable sensor readings found for radar chart farm_uuid={farm.farm_uuid if farm else None}.",
        )
    return {
        "labels": labels,
        "series": [{"name": "اکنون", "data": scores}, {"name": "هدف", "data": [100.0] * len(labels)}],
        "status": "success",
        "source": "db",
    }


def get_sensor_7_in_1_comparison_chart_data(farm=None, context=None):
    context = _get_sensor_context(farm) if context is None else context
    history = list(reversed(context["history"][:MAX_CHART_POINTS]))
    moisture_points = [(log.created_at.strftime("%m/%d %H:%M"), readings.get("soil_moisture")) for log, readings in history if readings.get("soil_moisture") is not None]
    if not moisture_points:
        raise DeviceDataUnavailableError(
            error_code="no_comparison_data",
            message=f"No soil moisture history found for comparison chart farm_uuid={farm.farm_uuid if farm else None}.",
        )
    categories = [item[0] for item in moisture_points]
    values = [round(item[1], 2) for item in moisture_points]
    current_value = values[-1]
    baseline_value = values[0] if len(values) > 1 else 55.0
    percent_change = ((current_value - baseline_value) / baseline_value) * 100 if baseline_value else 0.0
    return {
        "currentValue": round(current_value, 2),
        "vsLastWeekValue": round(percent_change, 2),
        "vsLastWeek": f"{percent_change:+.1f}%",
        "categories": categories,
        "series": [{"name": "رطوبت خاک", "data": values}, {"name": "بازه هدف", "data": [55.0] * len(values)}],
        "status": "success",
        "source": "db",
    }


def _build_anomaly_item(field, value):
    lower = field["ideal_min"]
    upper = field["ideal_max"]
    if lower <= value <= upper:
        return None
    deviation = value - upper if value > upper else value - lower
    severity = "warning"
    span = max(upper - lower, 0.1)
    if abs(deviation) >= span * 0.5:
        severity = "error"
    sign = "+" if deviation > 0 else ""
    return {"sensor": field["label"], "value": _format_value(value, field["unit"]), "expected": _format_range(field), "deviation": f"{sign}{_format_value(deviation, field['unit'])}", "severity": severity}


def get_sensor_7_in_1_anomaly_detection_card_data(farm=None, context=None):
    context = _get_sensor_context(farm) if context is None else context
    anomalies = []
    for field in SENSOR_FIELDS:
        value = context["latest_readings"].get(field["id"])
        if value is None:
            continue
        anomaly = _build_anomaly_item(field, value)
        if anomaly is not None:
            anomalies.append(anomaly)
    return {
        "anomalies": anomalies,
        "status": "success",
        "source": "db",
        "warnings": [] if anomalies else ["No anomalies detected from the latest sensor readings."],
    }


def get_sensor_7_in_1_soil_moisture_heatmap_data(farm=None, context=None):
    context = _get_sensor_context(farm) if context is None else context
    history = list(reversed(context["history"][:MAX_CHART_POINTS]))
    chart_points = [{"x": log.created_at.strftime("%H:%M"), "y": round(readings.get("soil_moisture"), 2)} for log, readings in history if readings.get("soil_moisture") is not None]
    if not chart_points:
        raise DeviceDataUnavailableError(
            error_code="no_heatmap_data",
            message=f"No soil moisture history found for heatmap farm_uuid={farm.farm_uuid if farm else None}.",
        )
    sensor_name = (
        SOIL_MOISTURE_HEATMAP_TEMPLATE["zones"][0]
        if SOIL_MOISTURE_HEATMAP_TEMPLATE["zones"]
        else "سنسور خاک"
    )
    farm_device = context.get("farm_device")
    if farm_device is not None and farm_device.name:
        sensor_name = farm_device.name
    return {
        "zones": [sensor_name],
        "hours": [point["x"] for point in chart_points],
        "series": [{"name": sensor_name, "data": chart_points}],
        "status": "success",
        "source": "db",
    }


def get_sensor_7_in_1_summary_data(farm=None):
    context = _get_sensor_context(farm)
    values_list = get_sensor_7_in_1_values_list_data(farm, context=context)
    return {"sensor": values_list["sensor"], "sensorValuesList": values_list, "avgSoilMoisture": get_sensor_7_in_1_avg_soil_moisture_data(farm, context=context), "sensorRadarChart": get_sensor_7_in_1_radar_chart_data(farm, context=context), "sensorComparisonChart": get_sensor_7_in_1_comparison_chart_data(farm, context=context), "anomalyDetectionCard": get_sensor_7_in_1_anomaly_detection_card_data(farm, context=context), "soilMoistureHeatmap": get_sensor_7_in_1_soil_moisture_heatmap_data(farm, context=context)}


def _normalize_comparison_chart_field(field_name):
    return COMPARISON_CHART_FIELD_ALIASES.get(field_name, field_name)


def _format_comparison_category(bucket_date, range_value):
    return PERSIAN_WEEKDAYS[bucket_date.weekday()] if range_value == "7d" else bucket_date.strftime("%m/%d")


def _format_percent_change(current_value, baseline_value):
    if not baseline_value:
        return "+0.0%"
    return f"{((current_value - baseline_value) / baseline_value) * 100:+.1f}%"


def _format_current_value_subtitle(title, value, unit):
    rendered_value = _format_value(value, unit)
    return f"مقدار فعلی: {rendered_value or title}"


def get_sensor_comparison_chart_data(*, farm, physical_device_uuid, range_value):
    days = COMPARISON_CHART_RANGES[range_value]
    start_date = timezone.localdate() - timedelta(days=days - 1)
    try:
        logs_queryset = get_sensor_external_request_logs_for_farm(farm_uuid=farm.farm_uuid, physical_device_uuid=physical_device_uuid, date_from=start_date)
    except ValueError as exc:
        raise DeviceDataUnavailableError(
            f"Sensor comparison chart data is unavailable for farm_uuid={farm.farm_uuid} device={physical_device_uuid}."
        ) from exc
    grouped_logs = {}
    for log in reversed(list(logs_queryset[: days * 24])):
        bucket_date = timezone.localtime(log.created_at).date()
        numeric_payload = _extract_numeric_payload(log.payload)
        if numeric_payload:
            grouped_logs[bucket_date] = numeric_payload
    if not grouped_logs:
        raise DeviceDataUnavailableError(
            f"No sensor history found for comparison chart farm_uuid={farm.farm_uuid} device={physical_device_uuid}."
        )
    sorted_dates = sorted(grouped_logs.keys())
    categories = [_format_comparison_category(bucket_date, range_value) for bucket_date in sorted_dates]
    series_map = {}
    for bucket_date in sorted_dates:
        normalized_payload = {_normalize_comparison_chart_field(key): value for key, value in grouped_logs[bucket_date].items()}
        for key, value in normalized_payload.items():
            series_map.setdefault(key, []).append(round(value, 2))
    ordered_field_names = [field_name for field_name in COMPARISON_CHART_PRIMARY_FIELDS if field_name in series_map] + sorted(field_name for field_name in series_map if field_name not in COMPARISON_CHART_PRIMARY_FIELDS)
    series = [{"name": field_name, "data": series_map[field_name]} for field_name in ordered_field_names]
    primary_data = series_map[ordered_field_names[0]]
    return {"series": series, "categories": categories, "currentValue": round(primary_data[-1], 2), "vsLastWeek": _format_percent_change(primary_data[-1], primary_data[0])}


def get_sensor_values_list_data(*, farm, physical_device_uuid, range_value):
    start_time = timezone.now() - VALUES_LIST_RANGES[range_value]
    try:
        logs_queryset = get_sensor_external_request_logs_for_farm(farm_uuid=farm.farm_uuid, physical_device_uuid=physical_device_uuid)
    except ValueError as exc:
        raise DeviceDataUnavailableError(
            f"Sensor values list data is unavailable for farm_uuid={farm.farm_uuid} device={physical_device_uuid}."
        ) from exc
    logs = list(logs_queryset.filter(created_at__gte=start_time).order_by("created_at", "id"))
    if not logs:
        latest_log = logs_queryset.order_by("-created_at", "-id").first()
        if latest_log is None:
            raise DeviceDataUnavailableError(
                f"No sensor logs found for values list farm_uuid={farm.farm_uuid} device={physical_device_uuid}."
            )
        logs = [latest_log]
    earliest_payload, latest_payload = {}, {}
    for log in logs:
        numeric_payload = {_normalize_comparison_chart_field(key): value for key, value in _extract_numeric_payload(log.payload).items()}
        if not numeric_payload:
            continue
        if not earliest_payload:
            earliest_payload = numeric_payload
        latest_payload = numeric_payload
    if not latest_payload:
        raise DeviceDataUnavailableError(
            f"Latest sensor payload has no numeric values for farm_uuid={farm.farm_uuid} device={physical_device_uuid}."
        )
    sensors = []
    for field_name, title, unit in VALUES_LIST_FIELDS:
        current_value = latest_payload.get(field_name)
        if current_value is None:
            continue
        previous_value = earliest_payload.get(field_name, current_value)
        delta = round(current_value - previous_value, 2)
        sensors.append({"title": title, "subtitle": _format_current_value_subtitle(title, current_value, unit), "trendNumber": abs(delta), "trend": "positive" if delta >= 0 else "negative", "unit": unit})
    return {"sensors": sensors}


def get_sensor_radar_chart_data(*, farm, physical_device_uuid, range_value):
    start_time = timezone.now() - RADAR_CHART_RANGES[range_value]
    try:
        logs_queryset = get_sensor_external_request_logs_for_farm(farm_uuid=farm.farm_uuid, physical_device_uuid=physical_device_uuid)
    except ValueError as exc:
        raise DeviceDataUnavailableError(
            f"Sensor radar chart data is unavailable for farm_uuid={farm.farm_uuid} device={physical_device_uuid}."
        ) from exc
    logs = list(logs_queryset.filter(created_at__gte=start_time).order_by("created_at", "id"))
    if not logs:
        latest_log = logs_queryset.order_by("-created_at", "-id").first()
        if latest_log is None:
            raise DeviceDataUnavailableError(
                f"No sensor logs found for radar chart farm_uuid={farm.farm_uuid} device={physical_device_uuid}."
            )
        logs = [latest_log]
    latest_payload = {}
    for log in logs:
        numeric_payload = {_normalize_comparison_chart_field(key): value for key, value in _extract_numeric_payload(log.payload).items()}
        if numeric_payload:
            latest_payload = numeric_payload
    if not latest_payload:
        raise DeviceDataUnavailableError(
            f"Latest sensor payload has no numeric values for radar chart farm_uuid={farm.farm_uuid} device={physical_device_uuid}."
        )
    labels, current_data, ideal_data = [], [], []
    for field_name, label, ideal_value in RADAR_CHART_FIELDS:
        current_value = latest_payload.get(field_name)
        if current_value is None:
            continue
        labels.append(label)
        current_data.append(round(current_value, 2))
        ideal_data.append(round(ideal_value, 2))
    return {"labels": labels, "series": [{"name": "وضعیت فعلی", "data": current_data}, {"name": "بازه ایده آل", "data": ideal_data}]}


DEVICE_COMMAND_PAYLOAD_TYPES = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "object": dict,
    "array": list,
}
DEFAULT_DEVICE_WIDGETS = [
    "values_list",
    "comparison_chart",
    "radar_chart",
    "latest_payload",
    "anomaly_card",
    "soil_moisture_heatmap",
]


def get_farm_device_by_physical_uuid(*, physical_device_uuid, owner=None):
    queryset = FarmDevice.objects.select_related("farm", "sensor_catalog").filter(physical_device_uuid=physical_device_uuid)
    if owner is not None:
        queryset = queryset.filter(farm__owner=owner)
    return queryset.first()


def get_device_catalog_for_farm_device(farm_device, *, device_code=None):
    if farm_device is None:
        return None
    if device_code:
        return farm_device.get_device_catalog_by_code(device_code)
    return farm_device.sensor_catalog if farm_device.sensor_catalog_id else (farm_device.get_device_catalogs()[0] if farm_device.get_device_catalogs() else None)


def get_latest_device_log(farm_device, *, device_catalog=None):
    if farm_device is None:
        return None
    return get_latest_sensor_external_request_log(
        farm_uuid=farm_device.farm.farm_uuid,
        sensor_catalog_uuid=device_catalog.uuid if device_catalog else (farm_device.sensor_catalog.uuid if farm_device.sensor_catalog else None),
        physical_device_uuid=farm_device.physical_device_uuid,
    )


def get_device_logs(farm_device, *, range_value=None, date_from=None, date_to=None):
    if farm_device is None:
        return SensorExternalRequestLog.objects.none()
    if range_value:
        date_from = timezone.localdate() - timedelta(days=max(range_value - 1, 0))
    return get_sensor_external_request_logs_for_farm(
        farm_uuid=farm_device.farm.farm_uuid,
        physical_device_uuid=farm_device.physical_device_uuid,
        date_from=date_from,
        date_to=date_to,
    )


def validate_output_device_catalog(*, farm_device, device_code):
    device_catalog = get_device_catalog_for_farm_device(farm_device, device_code=device_code)
    if device_catalog is None:
        raise ValueError("Device code is not attached to this farm device.")
    if device_catalog.device_communication_type == "input_only":
        raise ValueError("Selected device code is input-only and cannot be used for output data endpoints.")
    return device_catalog


def _get_default_field_definition_map():
    return {field["id"]: field for field in SENSOR_FIELDS}


def _normalize_payload_keys(payload_keys):
    if isinstance(payload_keys, str):
        return [payload_keys]
    if isinstance(payload_keys, (list, tuple)):
        return [item for item in payload_keys if isinstance(item, str) and item]
    return []


def _get_device_field_definitions(device_catalog):
    default_field_map = _get_default_field_definition_map()
    if device_catalog is None:
        return list(default_field_map.values())

    payload_mapping = device_catalog.payload_mapping if isinstance(device_catalog.payload_mapping, dict) else {}
    display_schema = device_catalog.display_schema if isinstance(device_catalog.display_schema, dict) else {}
    display_fields = display_schema.get("fields", []) if isinstance(display_schema.get("fields", []), list) else []

    ordered_ids = []
    for item in display_fields:
        if isinstance(item, dict) and item.get("id"):
            ordered_ids.append(item["id"])
    for item in device_catalog.returned_data_fields:
        if isinstance(item, str) and item not in ordered_ids:
            ordered_ids.append(item)
    for item in payload_mapping.keys():
        if item not in ordered_ids:
            ordered_ids.append(item)
    if not ordered_ids:
        ordered_ids = list(default_field_map.keys())

    display_field_map = {
        item["id"]: item for item in display_fields if isinstance(item, dict) and item.get("id")
    }
    field_definitions = []
    for field_id in ordered_ids:
        default_field = default_field_map.get(field_id, {})
        display_field = display_field_map.get(field_id, {})
        payload_keys = _normalize_payload_keys(payload_mapping.get(field_id)) or list(default_field.get("payload_keys", [])) or [field_id]
        field_definitions.append(
            {
                "id": field_id,
                "label": display_field.get("label") or default_field.get("label") or field_id.replace("_", " ").title(),
                "unit": display_field.get("unit") or default_field.get("unit") or "",
                "payload_keys": payload_keys,
                "ideal_min": display_field.get("ideal_min", default_field.get("ideal_min", 0.0)),
                "ideal_max": display_field.get("ideal_max", default_field.get("ideal_max", 100.0)),
                "radar_label": display_field.get("radar_label") or default_field.get("radar_label") or display_field.get("label") or default_field.get("label") or field_id,
            }
        )
    return field_definitions


def _extract_payload_with_field_definitions(payload, field_definitions):
    if not isinstance(payload, dict):
        return {}
    if isinstance(payload.get("payload"), dict):
        payload = payload["payload"]
    expected_keys = {key for field in field_definitions for key in field.get("payload_keys", [])}
    if isinstance(payload.get("data"), dict):
        nested = payload["data"]
        if not expected_keys or any(key in nested for key in expected_keys):
            payload = nested
    return payload


def normalize_device_payload(device_catalog, payload):
    field_definitions = _get_device_field_definitions(device_catalog)
    payload = _extract_payload_with_field_definitions(payload, field_definitions)
    normalized_payload = {}
    for field in field_definitions:
        for key in field["payload_keys"]:
            if key in payload:
                normalized_payload[field["id"]] = payload[key]
                break
    return normalized_payload


def extract_device_readings(device_catalog, payload):
    normalized_payload = normalize_device_payload(device_catalog, payload)
    readings = {}
    for key, value in normalized_payload.items():
        numeric_value = _to_float(value)
        if numeric_value is not None:
            readings[key] = numeric_value
    return readings


def _get_device_supported_widgets(device_catalog):
    if device_catalog is None:
        return list(DEFAULT_DEVICE_WIDGETS)
    widgets = device_catalog.supported_widgets if isinstance(device_catalog.supported_widgets, list) else []
    if widgets:
        return widgets
    if device_catalog.device_communication_type == "input_only":
        return []
    return list(DEFAULT_DEVICE_WIDGETS)


def _get_device_history_context(farm_device):
    if farm_device is None:
        raise DeviceDataUnavailableError(
            error_code="device_not_found",
            message="Farm device instance is required for history lookup.",
        )
    try:
        logs_queryset = get_device_logs(farm_device)
    except ValueError as exc:
        logger.error(
            "Device history lookup failed for farm_device_id=%s: %s",
            getattr(farm_device, "id", None),
            exc,
        )
        raise DeviceDataUnavailableError(
            error_code="history_unavailable",
            message=f"Device history lookup failed for farm_device_id={getattr(farm_device, 'id', None)}.",
            details={"farm_device_id": getattr(farm_device, "id", None)},
            retriable=True,
        ) from exc
    history = []
    device_catalog = get_device_catalog_for_farm_device(farm_device)
    for log in logs_queryset[:MAX_HISTORY_ITEMS]:
        readings = extract_device_readings(device_catalog, log.payload)
        normalized_payload = normalize_device_payload(device_catalog, log.payload)
        if readings or normalized_payload:
            history.append((log, readings, normalized_payload))
    if not history:
        raise DeviceDataUnavailableError(
            error_code="no_device_history",
            message=f"No device history found for farm_device_id={getattr(farm_device, 'id', None)}.",
            details={"farm_device_id": getattr(farm_device, "id", None)},
        )
    latest_log, latest_readings, latest_payload = history[0]
    return {
        "farm_device": farm_device,
        "latest_log": latest_log,
        "latest_readings": latest_readings,
        "latest_payload": latest_payload,
        "previous_readings": history[1][1] if len(history) > 1 else {},
        "history": history,
    }


def build_device_meta(farm_device, context=None, *, device_catalog=None):
    device_catalog = device_catalog or get_device_catalog_for_farm_device(farm_device)
    latest_log = (context or {}).get("latest_log")
    return {
        "name": farm_device.name if farm_device else "",
        "physicalDeviceUuid": str(farm_device.physical_device_uuid) if farm_device else None,
        "sensorCatalogCode": device_catalog.code if device_catalog else "",
        "updatedAt": latest_log.created_at.isoformat() if latest_log else None,
    }


def build_device_latest_payload(farm_device, *, device_code):
    device_catalog = validate_output_device_catalog(farm_device=farm_device, device_code=device_code)
    latest_log = get_latest_device_log(farm_device, device_catalog=device_catalog)
    if latest_log is None:
        raise DeviceDataUnavailableError(
            error_code="no_device_payload",
            message=f"No device payload log found for farm_device_id={getattr(farm_device, 'id', None)} device_code={device_code}.",
            details={"farm_device_id": getattr(farm_device, "id", None), "device_code": device_code},
        )
    return {
        "physical_device_uuid": farm_device.physical_device_uuid,
        "device_code": device_code,
        "device_catalog_code": device_catalog.code if device_catalog else None,
        "raw_payload": latest_log.payload,
        "normalized_payload": normalize_device_payload(device_catalog, latest_log.payload),
        "readings": extract_device_readings(device_catalog, latest_log.payload),
        "created_at": latest_log.created_at,
    }


def build_device_values_list(farm_device, range_value, *, device_code):
    try:
        logs_queryset = get_device_logs(farm_device)
    except ValueError as exc:
        raise DeviceDataUnavailableError(
            error_code="history_unavailable",
            message=f"Device values list data is unavailable for farm_device_id={getattr(farm_device, 'id', None)} device_code={device_code}.",
            details={"farm_device_id": getattr(farm_device, "id", None), "device_code": device_code},
            retriable=True,
        ) from exc
    start_time = timezone.now() - VALUES_LIST_RANGES[range_value]
    logs = list(logs_queryset.filter(created_at__gte=start_time).order_by("created_at", "id"))
    if not logs:
        latest_log = logs_queryset.order_by("-created_at", "-id").first()
        if latest_log is None:
            raise DeviceDataUnavailableError(
                error_code="no_device_history",
                message=f"No device logs found for values list farm_device_id={getattr(farm_device, 'id', None)} device_code={device_code}.",
                details={"farm_device_id": getattr(farm_device, "id", None), "device_code": device_code},
            )
        logs = [latest_log]
    device_catalog = validate_output_device_catalog(farm_device=farm_device, device_code=device_code)
    earliest_payload = {}
    latest_payload = {}
    for log in logs:
        normalized_payload = extract_device_readings(device_catalog, log.payload)
        if not normalized_payload:
            continue
        if not earliest_payload:
            earliest_payload = normalized_payload
        latest_payload = normalized_payload
    if not latest_payload:
        raise DeviceDataUnavailableError(
            error_code="no_numeric_readings",
            message=f"Latest device payload has no numeric values for farm_device_id={getattr(farm_device, 'id', None)} device_code={device_code}.",
            details={"farm_device_id": getattr(farm_device, "id", None), "device_code": device_code},
        )
    sensors = []
    for field in _get_device_field_definitions(device_catalog):
        current_value = latest_payload.get(field["id"])
        if current_value is None:
            continue
        previous_value = earliest_payload.get(field["id"], current_value)
        delta = round(current_value - previous_value, 2)
        sensors.append(
            {
                "title": field["label"],
                "subtitle": _format_current_value_subtitle(field["label"], current_value, field["unit"]),
                "trendNumber": abs(delta),
                "trend": "positive" if delta >= 0 else "negative",
                "unit": field["unit"],
            }
        )
    if not sensors:
        raise DeviceDataUnavailableError(
            error_code="no_numeric_readings",
            message=f"No device values could be derived for farm_device_id={getattr(farm_device, 'id', None)} device_code={device_code}.",
            details={"farm_device_id": getattr(farm_device, "id", None), "device_code": device_code},
        )
    return {"sensors": sensors, "status": "success", "source": "db"}


def build_device_summary_values_list(farm_device, context=None, *, device_catalog=None):
    context = _get_device_history_context(farm_device) if context is None else context
    device_catalog = device_catalog or get_device_catalog_for_farm_device(farm_device)
    data = {"sensor": build_device_meta(farm_device, context), "sensors": []}
    latest_readings = context.get("latest_readings", {}) if context else {}
    previous_readings = context.get("previous_readings", {}) if context else {}
    for field in _get_device_field_definitions(device_catalog):
        value = latest_readings.get(field["id"])
        if value is None:
            continue
        previous = previous_readings.get(field["id"])
        change = 0.0 if previous is None else round(value - previous, 2)
        data["sensors"].append(
            {
                "id": field["id"],
                "title": _format_value(value, field["unit"]),
                "subtitle": field["label"],
                "trendNumber": abs(change),
                "trend": "positive" if change >= 0 else "negative",
                "unit": field["unit"],
            }
        )
    if not data["sensors"]:
        raise DeviceDataUnavailableError(
            error_code="no_numeric_readings",
            message=f"No summary values available for farm_device_id={getattr(farm_device, 'id', None)}.",
            details={"farm_device_id": getattr(farm_device, "id", None)},
        )
    return data


def build_device_radar_chart(farm_device, range_value=None, *, device_code):
    device_catalog = validate_output_device_catalog(farm_device=farm_device, device_code=device_code)
    context = _get_device_history_context(farm_device)
    if not context or not context.get("latest_readings"):
        raise DeviceDataUnavailableError(
            error_code="no_radar_data",
            message=f"Device radar chart data is unavailable for farm_device_id={getattr(farm_device, 'id', None)} device_code={device_code}.",
            details={"farm_device_id": getattr(farm_device, "id", None), "device_code": device_code},
        )
    labels, current_data, ideal_data = [], [], []
    for field in _get_device_field_definitions(device_catalog):
        current_value = context["latest_readings"].get(field["id"])
        if current_value is None:
            continue
        labels.append(field["radar_label"])
        current_data.append(round(current_value, 2))
        midpoint = (field["ideal_min"] + field["ideal_max"]) / 2
        ideal_data.append(round(midpoint, 2))
    if not labels:
        raise DeviceDataUnavailableError(
            error_code="no_radar_data",
            message=f"No usable readings found for radar chart farm_device_id={getattr(farm_device, 'id', None)} device_code={device_code}.",
            details={"farm_device_id": getattr(farm_device, "id", None), "device_code": device_code},
        )
    return {"labels": labels, "series": [{"name": "وضعیت فعلی", "data": current_data}, {"name": "بازه ایده آل", "data": ideal_data}], "status": "success", "source": "db"}


def build_device_comparison_chart(farm_device, range_value, *, device_code):
    days = COMPARISON_CHART_RANGES[range_value]
    start_date = timezone.localdate() - timedelta(days=days - 1)
    try:
        logs_queryset = get_device_logs(farm_device, date_from=start_date)
    except ValueError as exc:
        raise DeviceDataUnavailableError(
            error_code="history_unavailable",
            message=f"Device comparison chart data is unavailable for farm_device_id={getattr(farm_device, 'id', None)} device_code={device_code}.",
            details={"farm_device_id": getattr(farm_device, "id", None), "device_code": device_code},
            retriable=True,
        ) from exc
    device_catalog = validate_output_device_catalog(farm_device=farm_device, device_code=device_code)
    field_definitions = _get_device_field_definitions(device_catalog)
    grouped_logs = {}
    for log in reversed(list(logs_queryset[: days * 24])):
        bucket_date = timezone.localtime(log.created_at).date()
        grouped_logs[bucket_date] = extract_device_readings(device_catalog, log.payload)
    if not grouped_logs:
        raise DeviceDataUnavailableError(
            error_code="no_device_history",
            message=f"No device history found for comparison chart farm_device_id={getattr(farm_device, 'id', None)} device_code={device_code}.",
            details={"farm_device_id": getattr(farm_device, "id", None), "device_code": device_code},
        )
    sorted_dates = sorted(grouped_logs.keys())
    categories = [_format_comparison_category(bucket_date, range_value) for bucket_date in sorted_dates]
    series = []
    primary_data = []
    for field in field_definitions:
        data_points = []
        for bucket_date in sorted_dates:
            value = grouped_logs[bucket_date].get(field["id"])
            if value is None:
                data_points.append(0.0)
            else:
                data_points.append(round(value, 2))
        if any(point != 0.0 for point in data_points):
            series.append({"name": field["label"], "data": data_points})
            if not primary_data:
                primary_data = data_points
    if not series or not primary_data:
        raise DeviceDataUnavailableError(
            error_code="no_comparison_data",
            message=f"Device comparison chart has no usable numeric series for farm_device_id={getattr(farm_device, 'id', None)} device_code={device_code}.",
            details={"farm_device_id": getattr(farm_device, "id", None), "device_code": device_code},
        )
    return {
        "series": series,
        "categories": categories,
        "currentValue": round(primary_data[-1], 2),
        "vsLastWeek": _format_percent_change(primary_data[-1], primary_data[0]),
        "status": "success",
        "source": "db",
    }


def build_device_anomaly_detection_card(farm_device, context=None, *, device_catalog=None):
    context = _get_device_history_context(farm_device) if context is None else context
    device_catalog = device_catalog or get_device_catalog_for_farm_device(farm_device)
    anomalies = []
    latest_readings = context.get("latest_readings", {}) if context else {}
    for field in _get_device_field_definitions(device_catalog):
        value = latest_readings.get(field["id"])
        if value is None:
            continue
        anomaly = _build_anomaly_item(field, value)
        if anomaly is not None:
            anomalies.append(anomaly)
    if not latest_readings:
        raise DeviceDataUnavailableError(
            error_code="no_numeric_readings",
            message=f"No latest readings available for anomaly detection farm_device_id={getattr(farm_device, 'id', None)}.",
            details={"farm_device_id": getattr(farm_device, "id", None)},
        )
    return {
        "anomalies": anomalies,
        "status": "success",
        "source": "db",
        "warnings": [] if anomalies else ["No anomalies detected from the latest device readings."],
    }


def build_device_soil_moisture_heatmap(farm_device, context=None, *, device_catalog=None):
    context = _get_device_history_context(farm_device) if context is None else context
    if not context or not context.get("history"):
        raise DeviceDataUnavailableError(
            error_code="no_heatmap_data",
            message=f"Device heatmap data is unavailable for farm_device_id={getattr(farm_device, 'id', None)}.",
            details={"farm_device_id": getattr(farm_device, "id", None)},
        )
    device_catalog = device_catalog or get_device_catalog_for_farm_device(farm_device)
    field_definitions = _get_device_field_definitions(device_catalog)
    primary_field = field_definitions[0] if field_definitions else None
    if primary_field is None:
        raise DeviceDataUnavailableError(
            error_code="invalid_schema",
            message=f"Device field schema is missing for heatmap farm_device_id={getattr(farm_device, 'id', None)}.",
            details={"farm_device_id": getattr(farm_device, "id", None)},
        )
    chart_points = []
    for log, readings, _normalized_payload in reversed(context["history"][:MAX_CHART_POINTS]):
        value = readings.get(primary_field["id"])
        if value is None:
            continue
        chart_points.append({"x": log.created_at.strftime("%H:%M"), "y": round(value, 2)})
    if not chart_points:
        raise DeviceDataUnavailableError(
            error_code="no_heatmap_data",
            message=f"Device heatmap has no usable numeric series for farm_device_id={getattr(farm_device, 'id', None)}.",
            details={"farm_device_id": getattr(farm_device, "id", None)},
        )
    sensor_name = farm_device.name if farm_device and farm_device.name else "Sensor"
    return {
        "zones": [sensor_name],
        "hours": [point["x"] for point in chart_points],
        "series": [{"name": sensor_name, "data": chart_points}],
        "status": "success",
        "source": "db",
    }


def build_device_avg_primary_metric(farm_device, context=None, *, device_catalog=None):
    context = _get_device_history_context(farm_device) if context is None else context
    latest_readings = context.get("latest_readings", {}) if context else {}
    device_catalog = device_catalog or get_device_catalog_for_farm_device(farm_device)
    field_definitions = _get_device_field_definitions(device_catalog)
    primary_field = field_definitions[0] if field_definitions else None
    if primary_field is None:
        raise DeviceDataUnavailableError(
            error_code="invalid_schema",
            message=f"Device field schema is missing for farm_device_id={getattr(farm_device, 'id', None)}.",
            details={"farm_device_id": getattr(farm_device, "id", None)},
        )
    primary_value = latest_readings.get(primary_field["id"])
    if primary_value is None:
        raise DeviceDataUnavailableError(
            error_code="missing_primary_metric",
            message=f"Primary metric is missing for farm_device_id={getattr(farm_device, 'id', None)}.",
            details={"farm_device_id": getattr(farm_device, "id", None)},
        )
    chip_text, chip_color, avatar_color = _calculate_status_chip(primary_value)
    return {
        **deepcopy(AVG_SOIL_MOISTURE_TEMPLATE),
        "title": primary_field["label"],
        "stats": _format_value(primary_value, primary_field["unit"]),
        "chipText": chip_text,
        "chipColor": chip_color,
        "avatarColor": avatar_color,
        "status": "success",
        "source": "db",
    }


def build_device_summary(farm_device, *, device_code):
    context = _get_device_history_context(farm_device)
    device_catalog = validate_output_device_catalog(farm_device=farm_device, device_code=device_code)
    summary = {"sensor": build_device_meta(farm_device, context, device_catalog=device_catalog), "supportedWidgets": _get_device_supported_widgets(device_catalog)}
    if device_catalog and device_catalog.device_communication_type == "input_only":
        summary["commands"] = device_catalog.commands_schema if isinstance(device_catalog.commands_schema, list) else []
        return summary
    summary["sensorValuesList"] = build_device_summary_values_list(farm_device, context=context, device_catalog=device_catalog)
    if "comparison_chart" in summary["supportedWidgets"]:
        summary["sensorComparisonChart"] = build_device_comparison_chart(farm_device, "7d", device_code=device_code)
    if "radar_chart" in summary["supportedWidgets"]:
        summary["sensorRadarChart"] = build_device_radar_chart(farm_device, device_code=device_code)
    if "anomaly_card" in summary["supportedWidgets"]:
        summary["anomalyDetectionCard"] = build_device_anomaly_detection_card(farm_device, context=context, device_catalog=device_catalog)
    if "soil_moisture_heatmap" in summary["supportedWidgets"]:
        summary["soilMoistureHeatmap"] = build_device_soil_moisture_heatmap(farm_device, context=context, device_catalog=device_catalog)
    summary["avgSoilMoisture"] = build_device_avg_primary_metric(farm_device, context=context, device_catalog=device_catalog)
    return summary


def validate_device_command(farm_device, command, payload, *, device_code):
    device_catalog = validate_output_device_catalog(farm_device=farm_device, device_code=device_code)
    commands_schema = device_catalog.commands_schema if device_catalog and isinstance(device_catalog.commands_schema, list) else []
    if not commands_schema:
        raise ValueError("This device does not support commands.")
    matched_command = next(
        (item for item in commands_schema if isinstance(item, dict) and item.get("command") == command),
        None,
    )
    if matched_command is None:
        raise ValueError("Command is not supported for this device.")
    payload = payload or {}
    if not isinstance(payload, dict):
        raise ValueError("`payload` must be an object.")
    payload_schema = matched_command.get("payload_schema", {})
    if not isinstance(payload_schema, dict):
        return matched_command
    for key, expected_type in payload_schema.items():
        if key not in payload:
            raise ValueError(f"`{key}` is required for this command.")
        expected_python_type = DEVICE_COMMAND_PAYLOAD_TYPES.get(expected_type)
        if expected_python_type is None:
            continue
        if expected_type == "integer" and isinstance(payload[key], bool):
            raise ValueError(f"`{key}` must be of type {expected_type}.")
        if not isinstance(payload[key], expected_python_type):
            raise ValueError(f"`{key}` must be of type {expected_type}.")
    return matched_command


def execute_device_command(*, farm_device, device_code, command, payload=None):
    validate_device_command(farm_device, command, payload or {}, device_code=device_code)
    return {
        "physical_device_uuid": farm_device.physical_device_uuid,
        "device_code": device_code,
        "command": command,
        "status": "queued",
    }
