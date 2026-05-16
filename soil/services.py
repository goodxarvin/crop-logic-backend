from collections import defaultdict
from copy import deepcopy
from uuid import UUID

from crop_zoning.models import CropZone
from crop_zoning.services import ensure_farm_ai_clusters_synced
from device_hub.services import extract_device_readings, get_device_catalog_for_farm_device, get_latest_device_log
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
        cell.get("moisture")
        for cell in heatmap.get("grid_cells", [])
        if cell.get("moisture") is not None
    ]
    if not values:
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
    if farm is None:
        return deepcopy(SOIL_MOISTURE_HEATMAP)

    monitor_data = get_soil_monitor_data(farm)
    zones = monitor_data.get("zones", [])
    if not zones:
        ensure_farm_ai_clusters_synced(farm_uuid=farm.farm_uuid, owner=farm.owner)
        monitor_data = get_soil_monitor_data(farm)
        zones = monitor_data.get("zones", [])
    if not zones:
        return {
            "farm_uuid": str(farm.farm_uuid),
            "location": {},
            "current_sensor": {},
            "soil_profile": [],
            "timestamp": None,
            "grid_resolution": {"type": "zone"},
            "grid_cells": [],
            "sensor_points": [],
            "quality_legend": {
                "optimal": ">= 60",
                "moderate": "45-59",
                "low": "< 45",
            },
            "depth_layers": [],
            "model_metadata": {"source": "backend", "aggregation": "zone_soil_moisture"},
            "summary": {
                "total_clusters": 0,
                "monitored_clusters": 0,
                "message": "هیچ cluster فعالی برای این مزرعه ثبت نشده است.",
            },
        }

    grid_cells = []
    sensor_points = []
    latest_recorded_at = None

    for zone in zones:
        cluster_label = zone.get("zone_id")
        aggregated_metrics = zone.get("aggregated_metrics", {})
        moisture = aggregated_metrics.get("soil_moisture")
        grid_cells.append(
            {
                "zone_id": zone.get("zone_id"),
                "zone_uuid": zone.get("zone_uuid"),
                "cluster": cluster_label,
                "class": zone.get("status", {}).get("label"),
                "moisture": moisture,
                "soil_vv": aggregated_metrics.get("soil_vv"),
                "status": zone.get("status", {}),
                "center": zone.get("center", {}),
                "geometry": zone.get("geometry", {}),
            }
        )
        for sensor in zone.get("sensors", []):
            sensor_points.append(
                {
                    "zone_id": zone.get("zone_id"),
                    "cluster_uuid": sensor.get("cluster_uuid"),
                    "name": sensor.get("name"),
                    "physical_device_uuid": sensor.get("physical_device_uuid"),
                    "moisture": sensor.get("latest_readings", {}).get("soil_moisture"),
                    "location_metadata": sensor.get("location_metadata", {}),
                }
            )
            if sensor.get("latest_recorded_at") and (latest_recorded_at is None or sensor["latest_recorded_at"] > latest_recorded_at):
                latest_recorded_at = sensor["latest_recorded_at"]

    current_sensor = sensor_points[0] if sensor_points else {}
    monitored_clusters = sum(1 for cell in grid_cells if cell.get("moisture") is not None)
    return {
        "farm_uuid": str(farm.farm_uuid),
        "location": {"area_uuid": monitor_data.get("area_uuid")},
        "current_sensor": current_sensor,
        "soil_profile": [],
        "timestamp": latest_recorded_at,
        "grid_resolution": {"type": "zone"},
        "grid_cells": grid_cells,
        "sensor_points": sensor_points,
        "quality_legend": {
            "optimal": ">= 60",
            "moderate": "45-59",
            "low": "< 45",
        },
        "depth_layers": [],
        "model_metadata": {"source": "backend", "aggregation": "zone_soil_moisture"},
        "summary": {
            "total_clusters": len(grid_cells),
            "monitored_clusters": monitored_clusters,
            "message": f"رطوبت خاک فقط برای {len(grid_cells)} cluster/class مزرعه محاسبه شده است.",
        },
    }


def get_soil_summary_data(farm=None):
    return {
        "avgSoilMoisture": get_avg_soil_moisture_data(farm),
        "sensorRadarChart": get_sensor_radar_chart_data(farm),
        "sensorComparisonChart": get_sensor_comparison_chart_data(farm),
        "anomalyDetectionCard": get_anomaly_detection_card_data(farm),
        "soilMoistureHeatmap": get_soil_moisture_heatmap_data(farm),
    }


def _parse_uuid(value):
    if not value:
        return None
    try:
        return UUID(str(value))
    except (TypeError, ValueError, AttributeError):
        return None


def _build_zone_matching_keys(zone):
    keys = {str(zone.uuid), str(zone.zone_id)}
    zone_uuid = _parse_uuid(zone.zone_id)
    if zone_uuid is not None:
        keys.add(str(zone_uuid))
    return {key.lower() for key in keys if key}


def _build_sensor_matching_keys(sensor):
    location_metadata = sensor.location_metadata if isinstance(sensor.location_metadata, dict) else {}
    keys = {
        str(sensor.cluster_uuid) if sensor.cluster_uuid else None,
        str(location_metadata.get("zone") or ""),
        str(location_metadata.get("cluster_code") or ""),
        str(location_metadata.get("cluster_label") or ""),
    }
    return {key.lower() for key in keys if key}


def _get_crop_area_for_farm(farm):
    return farm.current_crop_area or farm.crop_areas.order_by("-created_at", "-id").first()


def _build_sensor_monitor_payload(sensor):
    device_catalog = get_device_catalog_for_farm_device(sensor)
    latest_log = get_latest_device_log(sensor, device_catalog=device_catalog)
    latest_payload = latest_log.payload if latest_log else {}
    latest_readings = extract_device_readings(device_catalog, latest_payload) if latest_log else {}
    return {
        "sensor_uuid": str(sensor.uuid),
        "physical_device_uuid": str(sensor.physical_device_uuid),
        "name": sensor.name,
        "sensor_type": sensor.sensor_type,
        "sensor_catalog_code": device_catalog.code if device_catalog else "",
        "cluster_uuid": str(sensor.cluster_uuid) if sensor.cluster_uuid else None,
        "location_metadata": sensor.location_metadata if isinstance(sensor.location_metadata, dict) else {},
        "latest_recorded_at": latest_log.created_at.isoformat() if latest_log else None,
        "latest_payload": latest_payload,
        "latest_readings": latest_readings,
    }


def _aggregate_zone_readings(sensor_payloads):
    aggregates = defaultdict(list)
    for sensor_payload in sensor_payloads:
        for key, value in sensor_payload.get("latest_readings", {}).items():
            aggregates[key].append(value)

    return {
        key: round(sum(values) / len(values), 2)
        for key, values in aggregates.items()
        if values
    }


def _build_moisture_status(average_moisture):
    if average_moisture is None:
        return {"label": "بدون داده", "color": "secondary"}
    if average_moisture >= 60:
        return {"label": "بهینه", "color": "success"}
    if average_moisture >= 45:
        return {"label": "متوسط", "color": "warning"}
    return {"label": "کم", "color": "error"}


def _get_zone_cluster_payload(zone):
    if zone is None:
        return {}
    analysis = getattr(zone, "analysis", None)
    raw_response = getattr(analysis, "raw_response", None)
    if not isinstance(raw_response, dict):
        return {}
    cluster_payload = raw_response.get("cluster_recommendation") or {}
    return cluster_payload if isinstance(cluster_payload, dict) else {}


def _get_zone_soil_vv(zone):
    cluster_payload = _get_zone_cluster_payload(zone)
    for key in ("satellite_metrics", "resolved_metrics", "sensor_metrics"):
        metrics = cluster_payload.get(key) or {}
        if isinstance(metrics, dict) and metrics.get("soil_vv") is not None:
            return metrics.get("soil_vv")
    return None


def _get_zone_ai_moisture(zone):
    cluster_payload = _get_zone_cluster_payload(zone)
    resolved_metrics = cluster_payload.get("resolved_metrics") or {}
    if isinstance(resolved_metrics, dict) and resolved_metrics.get("soil_moisture") is not None:
        return resolved_metrics.get("soil_moisture")
    return None


def get_soil_monitor_data(farm):
    crop_area = _get_crop_area_for_farm(farm)
    zones = list(
        CropZone.objects.filter(crop_area=crop_area)
        .select_related("water_need_layer", "soil_quality_layer", "cultivation_risk_layer", "analysis")
        .order_by("sequence", "id")
    ) if crop_area else []

    zone_payloads = []
    zone_match_map = {}

    for zone in zones:
        payload = {
            "zone_uuid": str(zone.uuid),
            "zone_id": zone.zone_id,
            "sequence": zone.sequence,
            "area_hectares": zone.area_hectares,
            "area_sqm": zone.area_sqm,
            "center": zone.center,
            "geometry": zone.geometry,
            "water_need": {
                "level": getattr(zone.water_need_layer, "level", ""),
                "value": getattr(zone.water_need_layer, "value", ""),
                "color": getattr(zone.water_need_layer, "color", ""),
            },
            "soil_quality": {
                "level": getattr(zone.soil_quality_layer, "level", ""),
                "score": getattr(zone.soil_quality_layer, "score", 0),
                "color": getattr(zone.soil_quality_layer, "color", ""),
            },
            "cultivation_risk": {
                "level": getattr(zone.cultivation_risk_layer, "level", ""),
                "color": getattr(zone.cultivation_risk_layer, "color", ""),
            },
            "sensors": [],
            "aggregated_metrics": {},
            "status": {"label": "بدون داده", "color": "secondary"},
        }
        zone_payloads.append(payload)
        for key in _build_zone_matching_keys(zone):
            zone_match_map[key] = payload

    unassigned_sensors = []
    sensors = list(farm.sensors.select_related("sensor_catalog").prefetch_related("device_catalogs").order_by("created_at", "id"))
    for sensor in sensors:
        sensor_payload = _build_sensor_monitor_payload(sensor)
        matched_zone = None
        for key in _build_sensor_matching_keys(sensor):
            matched_zone = zone_match_map.get(key)
            if matched_zone is not None:
                break

        if matched_zone is None:
            unassigned_sensors.append(sensor_payload)
            continue

        matched_zone["sensors"].append(sensor_payload)

    monitored_zones = 0
    for zone, zone_payload in zip(zones, zone_payloads):
        zone_payload["aggregated_metrics"] = _aggregate_zone_readings(zone_payload["sensors"])
        zone_payload["aggregated_metrics"]["soil_vv"] = _get_zone_soil_vv(zone)
        if zone_payload["aggregated_metrics"].get("soil_moisture") is None:
            zone_payload["aggregated_metrics"]["soil_moisture"] = _get_zone_ai_moisture(zone)
        zone_payload["status"] = _build_moisture_status(zone_payload["aggregated_metrics"].get("soil_moisture"))
        if zone_payload["sensors"] or zone_payload["aggregated_metrics"].get("soil_moisture") is not None:
            monitored_zones += 1

    return {
        "farm_uuid": str(farm.farm_uuid),
        "area_uuid": str(crop_area.uuid) if crop_area else None,
        "zone_count": len(zone_payloads),
        "monitored_zones": monitored_zones,
        "unassigned_sensor_count": len(unassigned_sensors),
        "zones": zone_payloads,
        "unassigned_sensors": unassigned_sensors,
    }
