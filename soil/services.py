from copy import deepcopy

from farm_alerts.models import AnomalyDetection

from .mock_data import (
    ANOMALY_DETECTION_CARD,
    AVG_SOIL_MOISTURE,
    SENSOR_COMPARISON_CHART,
    SENSOR_RADAR_CHART,
    SOIL_MOISTURE_HEATMAP,
)


def get_avg_soil_moisture_data(farm=None):
    data = deepcopy(AVG_SOIL_MOISTURE)
    heatmap = get_soil_moisture_heatmap_data(farm)
    values = [
        point.get("y")
        for series in heatmap.get("series", [])
        for point in series.get("data", [])
        if point.get("y") is not None
    ]

    if not values:
        return data

    average = round(sum(values) / len(values))
    data["stats"] = f"{average}%"
    if average >= 60:
        data["chipText"] = "بهینه"
        data["chipColor"] = "success"
    elif average >= 45:
        data["chipText"] = "متوسط"
        data["chipColor"] = "warning"
    else:
        data["chipText"] = "کم"
        data["chipColor"] = "error"
        data["avatarColor"] = "warning"

    return data


def get_sensor_radar_chart_data(farm=None):
    return deepcopy(SENSOR_RADAR_CHART)


def get_sensor_comparison_chart_data(farm=None):
    return deepcopy(SENSOR_COMPARISON_CHART)


def get_anomaly_detection_card_data(farm=None):
    if farm is None:
        return deepcopy(ANOMALY_DETECTION_CARD)

    anomalies = list(AnomalyDetection.objects.filter(farm=farm)[:10])
    if not anomalies:
        return deepcopy(ANOMALY_DETECTION_CARD)

    return {
        "anomalies": [
            {
                "sensor": anomaly.sensor,
                "value": anomaly.value,
                "expected": anomaly.expected,
                "deviation": anomaly.deviation,
                "severity": anomaly.severity,
            }
            for anomaly in anomalies
        ]
    }


def get_soil_moisture_heatmap_data(farm=None):
    return deepcopy(SOIL_MOISTURE_HEATMAP)


def get_soil_summary_data(farm=None):
    return {
        "avgSoilMoisture": get_avg_soil_moisture_data(farm),
        "sensorRadarChart": get_sensor_radar_chart_data(farm),
        "sensorComparisonChart": get_sensor_comparison_chart_data(farm),
        "anomalyDetectionCard": get_anomaly_detection_card_data(farm),
        "soilMoistureHeatmap": get_soil_moisture_heatmap_data(farm),
    }
