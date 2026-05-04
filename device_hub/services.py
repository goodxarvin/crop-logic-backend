from copy import deepcopy
from datetime import timedelta
import logging

from django.conf import settings
from django.db import OperationalError, ProgrammingError, transaction
from django.utils import timezone

from external_api_adapter import request as external_api_request
from external_api_adapter.exceptions import ExternalAPIRequestError
from notifications.services import create_notification_for_farm_uuid

from .mock_data import ANOMALY_DETECTION_CARD, AVG_SOIL_MOISTURE, SENSOR_COMPARISON_CHART, SENSOR_RADAR_CHART, SENSOR_VALUES_LIST, SOIL_MOISTURE_HEATMAP
from .models import FarmSensor, SensorExternalRequestLog

logger = logging.getLogger(__name__)


class FarmDataForwardError(Exception):
    pass

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
            physical_device_uuids = FarmSensor.objects.filter(farm__farm_uuid=farm_uuid, sensor_type=sensor_type).values_list("physical_device_uuid", flat=True)
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
        farm_sensor_queryset = FarmSensor.objects.select_related("farm", "sensor_catalog").filter(
            farm__farm_uuid__in={log.farm_uuid for log in logs},
            physical_device_uuid__in={log.physical_device_uuid for log in logs},
        ).order_by("-created_at", "-id")
        farm_sensor_map = {}
        for farm_sensor in farm_sensor_queryset:
            exact_key = (farm_sensor.farm.farm_uuid, farm_sensor.sensor_catalog.uuid if farm_sensor.sensor_catalog else None, farm_sensor.physical_device_uuid)
            fallback_key = (farm_sensor.farm.farm_uuid, None, farm_sensor.physical_device_uuid)
            farm_sensor_map.setdefault(exact_key, farm_sensor)
            farm_sensor_map.setdefault(fallback_key, farm_sensor)
        return farm_sensor_map
    except (ProgrammingError, OperationalError) as exc:
        raise ValueError("Sensor external API tables are not migrated.") from exc


def get_latest_sensor_external_request_log(*, farm_uuid, sensor_catalog_uuid, physical_device_uuid):
    try:
        return SensorExternalRequestLog.objects.filter(farm_uuid=farm_uuid, sensor_catalog_uuid=sensor_catalog_uuid, physical_device_uuid=physical_device_uuid).order_by("-created_at", "-id").first()
    except (ProgrammingError, OperationalError) as exc:
        raise ValueError("Sensor external API tables are not migrated.") from exc


def create_sensor_external_notification(*, physical_device_uuid, payload=None):
    payload = payload or {}
    sensor = FarmSensor.objects.select_related("farm", "farm__current_crop_area", "sensor_catalog").filter(physical_device_uuid=physical_device_uuid).first()
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
                metadata={"farm_uuid": str(sensor.farm.farm_uuid), "sensor_catalog_uuid": str(sensor.sensor_catalog.uuid) if sensor.sensor_catalog else None, "physical_device_uuid": str(sensor.physical_device_uuid), "payload": payload},
            )
    except (ProgrammingError, OperationalError) as exc:
        raise ValueError("Sensor external API tables are not migrated.") from exc


def forward_sensor_payload_to_farm_data(*, physical_device_uuid, payload=None):
    payload = payload or {}
    sensor = FarmSensor.objects.select_related("farm", "farm__current_crop_area", "sensor_catalog").filter(physical_device_uuid=physical_device_uuid).first()
    if sensor is None:
        raise ValueError("Physical device not found.")
    farm_boundary = _get_farm_boundary(sensor=sensor)
    api_key = getattr(settings, "FARM_DATA_API_KEY", "")
    if not api_key:
        raise FarmDataForwardError("FARM_DATA_API_KEY is not configured.")
    sensor_key = _get_sensor_key(sensor=sensor)
    normalized_sensor_payload = _normalize_sensor_payload(sensor_key=sensor_key, sensor_payload=payload)
    request_payload = {"farm_uuid": str(sensor.farm.farm_uuid), "farm_boundary": farm_boundary, "sensor_key": sensor_key, "sensor_payload": normalized_sensor_payload}
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


def _get_sensor_key(*, sensor):
    if sensor.sensor_catalog and sensor.sensor_catalog.code:
        return sensor.sensor_catalog.code
    return "sensor-7-1"


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
        return None
    primary_sensor = get_primary_soil_sensor(farm=farm)
    if primary_sensor is None:
        return None
    try:
        logs_queryset = get_sensor_external_request_logs_for_farm(farm_uuid=farm.farm_uuid, physical_device_uuid=primary_sensor.physical_device_uuid)
    except ValueError:
        return None
    history = []
    for log in logs_queryset[:MAX_HISTORY_ITEMS]:
        readings = _extract_readings(log.payload)
        if readings:
            history.append((log, readings))
    if not history:
        return None
    latest_log, latest_readings = history[0]
    farm_sensor_map = get_farm_sensor_map_for_logs(logs=[latest_log])
    farm_sensor = farm_sensor_map.get((latest_log.farm_uuid, latest_log.sensor_catalog_uuid, latest_log.physical_device_uuid)) or primary_sensor
    return {"farm_sensor": farm_sensor, "latest_log": latest_log, "latest_readings": latest_readings, "previous_readings": history[1][1] if len(history) > 1 else {}, "history": history}


def _build_sensor_meta(context, fallback_sensor):
    sensor = deepcopy(fallback_sensor)
    if not context:
        return sensor
    farm_sensor = context.get("farm_sensor")
    latest_log = context["latest_log"]
    sensor["physicalDeviceUuid"] = str(latest_log.physical_device_uuid)
    sensor["updatedAt"] = latest_log.created_at.isoformat()
    if farm_sensor is not None:
        sensor["name"] = farm_sensor.name or sensor["name"]
        if farm_sensor.sensor_catalog is not None:
            sensor["sensorCatalogCode"] = farm_sensor.sensor_catalog.code
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
    data = deepcopy(SENSOR_VALUES_LIST)
    context = _get_sensor_context(farm) if context is None else context
    data["sensor"] = _build_sensor_meta(context, data["sensor"])
    if not context:
        return data
    latest_readings = context["latest_readings"]
    previous_readings = context["previous_readings"]
    sensors = []
    for field in SENSOR_FIELDS:
        value = latest_readings.get(field["id"])
        if value is None:
            continue
        previous = previous_readings.get(field["id"])
        change = 0.0 if previous is None else round(value - previous, 2)
        sensors.append({"id": field["id"], "title": _format_value(value, field["unit"]), "subtitle": field["label"], "trendNumber": abs(change), "trend": "positive" if change >= 0 else "negative", "unit": field["unit"]})
    if sensors:
        data["sensors"] = sensors
    return data


def get_sensor_7_in_1_avg_soil_moisture_data(farm=None, context=None):
    data = deepcopy(AVG_SOIL_MOISTURE)
    context = _get_sensor_context(farm) if context is None else context
    if not context:
        return data
    moisture = context["latest_readings"].get("soil_moisture")
    if moisture is None:
        return data
    chip_text, chip_color, avatar_color = _calculate_status_chip(moisture)
    data["stats"] = _format_value(moisture, "%")
    data["chipText"] = chip_text
    data["chipColor"] = chip_color
    data["avatarColor"] = avatar_color
    return data


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
    data = deepcopy(SENSOR_RADAR_CHART)
    context = _get_sensor_context(farm) if context is None else context
    if not context:
        return data
    latest_readings = context["latest_readings"]
    scores, labels = [], []
    for field in SENSOR_FIELDS:
        value = latest_readings.get(field["id"])
        if value is None:
            continue
        labels.append(field["radar_label"])
        scores.append(_score_field(value, field))
    if labels:
        data["labels"] = labels
        data["series"] = [{"name": "اکنون", "data": scores}, {"name": "هدف", "data": [100.0] * len(labels)}]
    return data


def get_sensor_7_in_1_comparison_chart_data(farm=None, context=None):
    data = deepcopy(SENSOR_COMPARISON_CHART)
    context = _get_sensor_context(farm) if context is None else context
    if not context:
        return data
    history = list(reversed(context["history"][:MAX_CHART_POINTS]))
    moisture_points = [(log.created_at.strftime("%m/%d %H:%M"), readings.get("soil_moisture")) for log, readings in history if readings.get("soil_moisture") is not None]
    if not moisture_points:
        return data
    categories = [item[0] for item in moisture_points]
    values = [round(item[1], 2) for item in moisture_points]
    current_value = values[-1]
    baseline_value = values[0] if len(values) > 1 else 55.0
    percent_change = ((current_value - baseline_value) / baseline_value) * 100 if baseline_value else 0.0
    data["currentValue"] = round(current_value, 2)
    data["vsLastWeekValue"] = round(percent_change, 2)
    data["vsLastWeek"] = f"{percent_change:+.1f}%"
    data["categories"] = categories
    data["series"] = [{"name": "رطوبت خاک", "data": values}, {"name": "بازه هدف", "data": [55.0] * len(values)}]
    return data


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
    data = deepcopy(ANOMALY_DETECTION_CARD)
    context = _get_sensor_context(farm) if context is None else context
    if not context:
        return data
    anomalies = []
    for field in SENSOR_FIELDS:
        value = context["latest_readings"].get(field["id"])
        if value is None:
            continue
        anomaly = _build_anomaly_item(field, value)
        if anomaly is not None:
            anomalies.append(anomaly)
    data["anomalies"] = anomalies or [{"sensor": "سنسور 7 در 1 خاک", "value": "نرمال", "expected": "تمام شاخص‌ها در بازه مجاز هستند", "deviation": "0", "severity": "success"}]
    return data


def get_sensor_7_in_1_soil_moisture_heatmap_data(farm=None, context=None):
    data = deepcopy(SOIL_MOISTURE_HEATMAP)
    context = _get_sensor_context(farm) if context is None else context
    if not context:
        return data
    history = list(reversed(context["history"][:MAX_CHART_POINTS]))
    chart_points = [{"x": log.created_at.strftime("%H:%M"), "y": round(readings.get("soil_moisture"), 2)} for log, readings in history if readings.get("soil_moisture") is not None]
    if not chart_points:
        return data
    sensor_name = data["zones"][0]
    farm_sensor = context.get("farm_sensor")
    if farm_sensor is not None and farm_sensor.name:
        sensor_name = farm_sensor.name
    data["zones"] = [sensor_name]
    data["hours"] = [point["x"] for point in chart_points]
    data["series"] = [{"name": sensor_name, "data": chart_points}]
    return data


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
    except ValueError:
        return {"series": [], "categories": [], "currentValue": 0.0, "vsLastWeek": "+0.0%"}
    grouped_logs = {}
    for log in reversed(list(logs_queryset[: days * 24])):
        bucket_date = timezone.localtime(log.created_at).date()
        numeric_payload = _extract_numeric_payload(log.payload)
        if numeric_payload:
            grouped_logs[bucket_date] = numeric_payload
    if not grouped_logs:
        return {"series": [], "categories": [], "currentValue": 0.0, "vsLastWeek": "+0.0%"}
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
    except ValueError:
        return {"sensors": []}
    logs = list(logs_queryset.filter(created_at__gte=start_time).order_by("created_at", "id"))
    if not logs:
        latest_log = logs_queryset.order_by("-created_at", "-id").first()
        if latest_log is None:
            return {"sensors": []}
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
        return {"sensors": []}
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
    except ValueError:
        return {"labels": [], "series": []}
    logs = list(logs_queryset.filter(created_at__gte=start_time).order_by("created_at", "id"))
    if not logs:
        latest_log = logs_queryset.order_by("-created_at", "-id").first()
        if latest_log is None:
            return {"labels": [], "series": []}
        logs = [latest_log]
    latest_payload = {}
    for log in logs:
        numeric_payload = {_normalize_comparison_chart_field(key): value for key, value in _extract_numeric_payload(log.payload).items()}
        if numeric_payload:
            latest_payload = numeric_payload
    if not latest_payload:
        return {"labels": [], "series": []}
    labels, current_data, ideal_data = [], [], []
    for field_name, label, ideal_value in RADAR_CHART_FIELDS:
        current_value = latest_payload.get(field_name)
        if current_value is None:
            continue
        labels.append(label)
        current_data.append(round(current_value, 2))
        ideal_data.append(round(ideal_value, 2))
    return {"labels": labels, "series": [{"name": "وضعیت فعلی", "data": current_data}, {"name": "بازه ایده آل", "data": ideal_data}]}
