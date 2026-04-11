from copy import deepcopy

from sensor_external_api.services import get_farm_sensor_map_for_logs, get_sensor_external_request_logs_for_farm

from .mock_data import (
    ANOMALY_DETECTION_CARD,
    AVG_SOIL_MOISTURE,
    SENSOR_COMPARISON_CHART,
    SENSOR_RADAR_CHART,
    SENSOR_VALUES_LIST,
    SOIL_MOISTURE_HEATMAP,
)


SENSOR_FIELDS = [
    {
        "id": "soil_moisture",
        "label": "رطوبت خاک",
        "unit": "%",
        "payload_keys": ("soil_moisture", "soilMoisture", "moisture"),
        "ideal_min": 45.0,
        "ideal_max": 65.0,
        "radar_label": "رطوبت",
    },
    {
        "id": "soil_temperature",
        "label": "دمای خاک",
        "unit": "°C",
        "payload_keys": ("soil_temperature", "soilTemperature", "temperature"),
        "ideal_min": 18.0,
        "ideal_max": 28.0,
        "radar_label": "دما",
    },
    {
        "id": "soil_ph",
        "label": "pH خاک",
        "unit": "pH",
        "payload_keys": ("soil_ph", "soilPh", "ph"),
        "ideal_min": 6.0,
        "ideal_max": 7.5,
        "radar_label": "pH",
    },
    {
        "id": "electrical_conductivity",
        "label": "هدایت الکتریکی",
        "unit": "dS/m",
        "payload_keys": ("electrical_conductivity", "electricalConductivity", "ec"),
        "ideal_min": 0.8,
        "ideal_max": 1.8,
        "radar_label": "EC",
    },
    {
        "id": "nitrogen",
        "label": "نیتروژن",
        "unit": "mg/kg",
        "payload_keys": ("nitrogen", "n"),
        "ideal_min": 20.0,
        "ideal_max": 40.0,
        "radar_label": "نیتروژن",
    },
    {
        "id": "phosphorus",
        "label": "فسفر",
        "unit": "mg/kg",
        "payload_keys": ("phosphorus", "p"),
        "ideal_min": 10.0,
        "ideal_max": 25.0,
        "radar_label": "فسفر",
    },
    {
        "id": "potassium",
        "label": "پتاسیم",
        "unit": "mg/kg",
        "payload_keys": ("potassium", "k"),
        "ideal_min": 15.0,
        "ideal_max": 35.0,
        "radar_label": "پتاسیم",
    },
]

MIN_REQUIRED_SENSOR_FIELDS = 4
MAX_HISTORY_ITEMS = 20
MAX_CHART_POINTS = 7


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
    unit = field["unit"]
    if unit in {"", "pH"}:
        return f"{lower}-{upper}"
    return f"{lower}-{upper} {unit}"


def _get_sensor_context(farm=None):
    if farm is None:
        return None

    try:
        logs_queryset = get_sensor_external_request_logs_for_farm(farm_uuid=farm.farm_uuid)
    except ValueError:
        return None

    candidate_log = None
    candidate_readings = {}
    for log in logs_queryset[:MAX_HISTORY_ITEMS]:
        readings = _extract_readings(log.payload)
        if len(readings) >= MIN_REQUIRED_SENSOR_FIELDS:
            candidate_log = log
            candidate_readings = readings
            break

    if candidate_log is None:
        return None

    history = []
    for log in logs_queryset.filter(physical_device_uuid=candidate_log.physical_device_uuid)[:MAX_HISTORY_ITEMS]:
        readings = _extract_readings(log.payload)
        if readings:
            history.append((log, readings))

    if not history:
        history = [(candidate_log, candidate_readings)]

    farm_sensor_map = get_farm_sensor_map_for_logs(logs=[candidate_log])
    farm_sensor = farm_sensor_map.get(
        (candidate_log.farm_uuid, candidate_log.sensor_catalog_uuid, candidate_log.physical_device_uuid)
    )

    return {
        "farm_sensor": farm_sensor,
        "latest_log": history[0][0],
        "latest_readings": history[0][1],
        "previous_readings": history[1][1] if len(history) > 1 else {},
        "history": history,
    }


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
        sensors.append(
            {
                "id": field["id"],
                "title": _format_value(value, field["unit"]),
                "subtitle": field["label"],
                "trendNumber": abs(change),
                "trend": "positive" if change >= 0 else "negative",
                "unit": field["unit"],
            }
        )

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
    scores = []
    labels = []
    for field in SENSOR_FIELDS:
        value = latest_readings.get(field["id"])
        if value is None:
            continue
        labels.append(field["radar_label"])
        scores.append(_score_field(value, field))

    if labels:
        data["labels"] = labels
        data["series"] = [
            {"name": "اکنون", "data": scores},
            {"name": "هدف", "data": [100.0] * len(labels)},
        ]
    return data


def get_sensor_7_in_1_comparison_chart_data(farm=None, context=None):
    data = deepcopy(SENSOR_COMPARISON_CHART)
    context = _get_sensor_context(farm) if context is None else context
    if not context:
        return data

    history = list(reversed(context["history"][:MAX_CHART_POINTS]))
    moisture_points = [
        (log.created_at.strftime("%m/%d %H:%M"), readings.get("soil_moisture"))
        for log, readings in history
        if readings.get("soil_moisture") is not None
    ]
    if not moisture_points:
        return data

    categories = [item[0] for item in moisture_points]
    values = [round(item[1], 2) for item in moisture_points]
    current_value = values[-1]
    baseline_value = values[0] if len(values) > 1 else 55.0
    percent_change = 0.0
    if baseline_value:
        percent_change = ((current_value - baseline_value) / baseline_value) * 100

    data["currentValue"] = round(current_value, 2)
    data["vsLastWeekValue"] = round(percent_change, 2)
    data["vsLastWeek"] = f"{percent_change:+.1f}%"
    data["categories"] = categories
    data["series"] = [
        {"name": "رطوبت خاک", "data": values},
        {"name": "بازه هدف", "data": [55.0] * len(values)},
    ]
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
    return {
        "sensor": field["label"],
        "value": _format_value(value, field["unit"]),
        "expected": _format_range(field),
        "deviation": f"{sign}{_format_value(deviation, field['unit'])}",
        "severity": severity,
    }


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

    if anomalies:
        data["anomalies"] = anomalies
    else:
        data["anomalies"] = [
            {
                "sensor": "سنسور 7 در 1 خاک",
                "value": "نرمال",
                "expected": "تمام شاخص‌ها در بازه مجاز هستند",
                "deviation": "0",
                "severity": "success",
            }
        ]

    return data


def get_sensor_7_in_1_soil_moisture_heatmap_data(farm=None, context=None):
    data = deepcopy(SOIL_MOISTURE_HEATMAP)
    context = _get_sensor_context(farm) if context is None else context
    if not context:
        return data

    history = list(reversed(context["history"][:MAX_CHART_POINTS]))
    chart_points = [
        {"x": log.created_at.strftime("%H:%M"), "y": round(readings.get("soil_moisture"), 2)}
        for log, readings in history
        if readings.get("soil_moisture") is not None
    ]
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
    return {
        "sensor": values_list["sensor"],
        "sensorValuesList": values_list,
        "avgSoilMoisture": get_sensor_7_in_1_avg_soil_moisture_data(farm, context=context),
        "sensorRadarChart": get_sensor_7_in_1_radar_chart_data(farm, context=context),
        "sensorComparisonChart": get_sensor_7_in_1_comparison_chart_data(farm, context=context),
        "anomalyDetectionCard": get_sensor_7_in_1_anomaly_detection_card_data(farm, context=context),
        "soilMoistureHeatmap": get_sensor_7_in_1_soil_moisture_heatmap_data(farm, context=context),
    }
