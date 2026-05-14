import math
import hashlib
from copy import deepcopy
from decimal import Decimal
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from celery.result import AsyncResult
from kombu.exceptions import OperationalError
from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone
from farm_hub.models import FarmHub

from external_api_adapter.adapter import request as external_request

from .defaults import DEFAULT_AREA_FEATURE, DEFAULT_PRODUCTS_PAYLOAD
from .models import (
    CropArea,
    CropProduct,
    CropZone,
    CropZoneAnalysis,
    CropZoneCriteria,
    CropZoneCultivationRiskLayer,
    CropZoneRecommendation,
    CropZoneSoilQualityLayer,
    CropZoneWaterNeedLayer,
)

EARTH_RADIUS_METERS = 6378137.0
PRODUCT_DEFAULTS = DEFAULT_PRODUCTS_PAYLOAD["products"]
DEFAULT_CELL_SIDE_KM = 0.15
DEFAULT_ZONE_PAGE_SIZE = 10
RULE_BASED_ALGORITHM = "rule_based_v1"
RULE_BASED_PRODUCTS = {
    "wheat": {
        "water_need": "۴۵۰۰-۵۵۰۰ m³/ha",
        "water_need_level": "medium",
        "estimated_profit": "۱۵-۲۵ میلیون/هکتار",
        "reason": "دمای مناسب، خاک حاصلخیز، دسترسی به آب کافی",
    },
    "canola": {
        "water_need": "۵۰۰۰-۶۰۰۰ m³/ha",
        "water_need_level": "high",
        "estimated_profit": "۲۰-۳۵ میلیون/هکتار",
        "reason": "پایداری بهتر در برابر نوسان دما و پتانسیل سود اقتصادی مناسب",
    },
    "saffron": {
        "water_need": "۳۰۰۰-۴۰۰۰ m³/ha",
        "water_need_level": "low",
        "estimated_profit": "۵۰-۱۵۰ میلیون/هکتار",
        "reason": "اقلیم خشک‌تر و نیاز آبی کمتر این زون برای زعفران مناسب‌تر است",
    },
}
RULE_BASED_CROP_IDS = tuple(RULE_BASED_PRODUCTS.keys())
TASK_STATE_PENDING = "PENDING"
TASK_STATE_STARTED = "STARTED"
TASK_STATE_RETRY = "RETRY"
TASK_STATE_SUCCESS = "SUCCESS"
TASK_STATE_FAILURE = "FAILURE"
TASK_STATE_REVOKED = "REVOKED"
AI_LOCATION_DATA_PATH = "/api/location-data/"
AI_REMOTE_SENSING_PATH = "/api/location-data/remote-sensing/"
AI_CLUSTER_RECOMMENDATIONS_PATH = "/api/location-data/remote-sensing/cluster-recommendations/"


def get_default_cell_side_km():
    raw_value = getattr(settings, "CROP_ZONE_CELL_SIDE_KM", None)
    try:
        cell_side_km = float(raw_value)
    except (TypeError, ValueError):
        cell_side_km = 0
    if cell_side_km > 0:
        return cell_side_km

    raw_value = getattr(settings, "CROP_ZONE_CHUNK_AREA_SQM", 0)
    try:
        chunk_area = float(raw_value)
    except (TypeError, ValueError):
        chunk_area = 0
    if chunk_area > 0:
        return math.sqrt(chunk_area) / 1000.0

    return DEFAULT_CELL_SIDE_KM


def get_task_stale_seconds():
    raw_value = getattr(settings, "CROP_ZONE_TASK_STALE_SECONDS", 300)
    try:
        stale_seconds = int(raw_value)
    except (TypeError, ValueError):
        stale_seconds = 300
    return max(stale_seconds, 0)


def get_cell_side_km(cell_side_km=None):
    if cell_side_km is None or cell_side_km == "":
        resolved_value = get_default_cell_side_km()
    else:
        try:
            resolved_value = float(cell_side_km)
        except (TypeError, ValueError) as exc:
            raise ValueError("cell_side_km must be a positive number.") from exc

    if resolved_value <= 0:
        raise ValueError("cell_side_km must be a positive number.")
    return resolved_value


def get_chunk_area_sqm(cell_side_km=None):
    resolved_cell_side_km = get_cell_side_km(cell_side_km)
    return (resolved_cell_side_km * 1000.0) ** 2


def parse_positive_int(value, field_name, default=None):
    if value in {None, ""}:
        if default is None:
            raise ValueError(f"{field_name} must be a positive integer.")
        return default

    try:
        parsed_value = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a positive integer.") from exc

    if parsed_value <= 0:
        raise ValueError(f"{field_name} must be a positive integer.")
    return parsed_value


def get_zone_page_request_params(query_params):
    return (
        parse_positive_int(query_params.get("page"), "page", default=1),
        parse_positive_int(query_params.get("page_size"), "page_size", default=DEFAULT_ZONE_PAGE_SIZE),
    )


def get_default_area_feature():
    return deepcopy(DEFAULT_AREA_FEATURE["area"])


def normalize_area_feature(area_feature):
    if area_feature is None:
        raise ValueError("Area polygon coordinates are required.")
    if not isinstance(area_feature, dict):
        raise ValueError("Area GeoJSON must be an object.")

    if area_feature.get("type") == "Feature":
        geometry = deepcopy(area_feature.get("geometry") or {})
        normalized_feature = {
            "type": "Feature",
            "properties": deepcopy(area_feature.get("properties") or {}),
            "geometry": geometry,
        }
    else:
        normalized_feature = {
            "type": "Feature",
            "properties": {},
            "geometry": deepcopy(area_feature),
        }

    geometry = normalized_feature.get("geometry") or {}
    if geometry.get("type") != "Polygon":
        raise ValueError("Area GeoJSON geometry type must be Polygon.")

    ring = get_polygon_ring(normalized_feature)
    if len(ring) < 4:
        raise ValueError("Area polygon must contain at least four coordinates.")

    return normalized_feature


def ensure_products_exist():
    for product in PRODUCT_DEFAULTS:
        CropProduct.objects.update_or_create(
            product_id=product["id"],
            defaults={"label": product["label"], "color": product["color"]},
        )


def get_products_payload():
    ensure_products_exist()
    products = CropProduct.objects.order_by("id")
    return {
        "products": [
            {"id": product.product_id, "label": product.label, "color": product.color}
            for product in products
        ]
    }


def get_polygon_ring(area_feature):
    geometry = (area_feature or {}).get("geometry", {})
    coordinates = geometry.get("coordinates", [])
    if not coordinates or not coordinates[0]:
        raise ValueError("Area polygon coordinates are required.")
    return coordinates[0]


def polygon_area_sqm(ring):
    if len(ring) < 4:
        return 0.0

    latitudes = [point[1] for point in ring]
    mean_latitude = math.radians(sum(latitudes) / len(latitudes))

    projected_points = []
    for longitude, latitude in ring:
        x = math.radians(longitude) * EARTH_RADIUS_METERS * math.cos(mean_latitude)
        y = math.radians(latitude) * EARTH_RADIUS_METERS
        projected_points.append((x, y))

    area = 0.0
    for index in range(len(projected_points) - 1):
        x1, y1 = projected_points[index]
        x2, y2 = projected_points[index + 1]
        area += (x1 * y2) - (x2 * y1)

    return abs(area) / 2.0


def normalize_points(ring):
    if len(ring) > 1 and ring[0] == ring[-1]:
        ring = ring[:-1]
    return [[point[0], point[1]] for point in ring]


def calculate_center(points):
    if not points:
        return {"longitude": 0.0, "latitude": 0.0}

    longitude = sum(point[0] for point in points) / len(points)
    latitude = sum(point[1] for point in points) / len(points)
    return {
        "longitude": round(longitude, 8),
        "latitude": round(latitude, 8),
    }


def get_bbox(points):
    longitudes = [point[0] for point in points]
    latitudes = [point[1] for point in points]
    return {
        "min_lng": min(longitudes),
        "max_lng": max(longitudes),
        "min_lat": min(latitudes),
        "max_lat": max(latitudes),
    }


def meters_to_latitude_delta(meters):
    return meters / 111320.0


def meters_to_longitude_delta(meters, latitude):
    longitude_factor = 111320.0 * math.cos(math.radians(latitude))
    if abs(longitude_factor) < 1e-9:
        longitude_factor = 1.0
    return meters / longitude_factor


def point_in_polygon(point, polygon_points):
    x, y = point
    inside = False
    point_count = len(polygon_points)
    if point_count < 3:
        return False

    for index in range(point_count):
        x1, y1 = polygon_points[index]
        x2, y2 = polygon_points[(index + 1) % point_count]
        intersects = ((y1 > y) != (y2 > y)) and (
            x < ((x2 - x1) * (y - y1) / ((y2 - y1) or 1e-12)) + x1
        )
        if intersects:
            inside = not inside

    return inside


def _orientation(point_a, point_b, point_c):
    value = ((point_b[1] - point_a[1]) * (point_c[0] - point_b[0])) - (
        (point_b[0] - point_a[0]) * (point_c[1] - point_b[1])
    )
    if abs(value) < 1e-12:
        return 0
    return 1 if value > 0 else 2


def _on_segment(point_a, point_b, point_c):
    return (
        min(point_a[0], point_c[0]) - 1e-12 <= point_b[0] <= max(point_a[0], point_c[0]) + 1e-12
        and min(point_a[1], point_c[1]) - 1e-12 <= point_b[1] <= max(point_a[1], point_c[1]) + 1e-12
    )


def segments_intersect(point_a, point_b, point_c, point_d):
    orientation_1 = _orientation(point_a, point_b, point_c)
    orientation_2 = _orientation(point_a, point_b, point_d)
    orientation_3 = _orientation(point_c, point_d, point_a)
    orientation_4 = _orientation(point_c, point_d, point_b)

    if orientation_1 != orientation_2 and orientation_3 != orientation_4:
        return True

    if orientation_1 == 0 and _on_segment(point_a, point_c, point_b):
        return True
    if orientation_2 == 0 and _on_segment(point_a, point_d, point_b):
        return True
    if orientation_3 == 0 and _on_segment(point_c, point_a, point_d):
        return True
    if orientation_4 == 0 and _on_segment(point_c, point_b, point_d):
        return True

    return False


def rectangle_contains_point(point, cell_points):
    min_lng = min(vertex[0] for vertex in cell_points)
    max_lng = max(vertex[0] for vertex in cell_points)
    min_lat = min(vertex[1] for vertex in cell_points)
    max_lat = max(vertex[1] for vertex in cell_points)
    return min_lng <= point[0] <= max_lng and min_lat <= point[1] <= max_lat


def polygon_intersects_cell(polygon_points, cell_points):
    cell_center = calculate_center(cell_points)
    if point_in_polygon([cell_center["longitude"], cell_center["latitude"]], polygon_points):
        return True

    if any(point_in_polygon(point, polygon_points) for point in cell_points):
        return True

    if any(rectangle_contains_point(point, cell_points) for point in polygon_points):
        return True

    polygon_edges = list(zip(polygon_points, polygon_points[1:] + polygon_points[:1]))
    cell_edges = list(zip(cell_points, cell_points[1:] + cell_points[:1]))
    return any(
        segments_intersect(start_a, end_a, start_b, end_b)
        for start_a, end_a in polygon_edges
        for start_b, end_b in cell_edges
    )


def build_square_points(left_lng, bottom_lat, right_lng, top_lat):
    return [
        [round(left_lng, 8), round(bottom_lat, 8)],
        [round(right_lng, 8), round(bottom_lat, 8)],
        [round(right_lng, 8), round(top_lat, 8)],
        [round(left_lng, 8), round(top_lat, 8)],
    ]


def build_zone_square(area_points, center, zone_area_sqm):
    if len(area_points) < 4:
        return area_points

    width = math.sqrt(max(zone_area_sqm, 1))
    half_width = width / 2.0
    delta_lat = meters_to_latitude_delta(half_width)
    delta_lng = meters_to_longitude_delta(half_width, center["latitude"])

    return build_square_points(
        center["longitude"] - delta_lng,
        center["latitude"] - delta_lat,
        center["longitude"] + delta_lng,
        center["latitude"] + delta_lat,
    )


def split_area_into_zones(area_feature, cell_side_km=None):
    area_ring = get_polygon_ring(area_feature)
    area_points = normalize_points(area_ring)
    area_center = calculate_center(area_points)
    total_area_sqm = polygon_area_sqm(area_ring)
    resolved_cell_side_km = get_cell_side_km(cell_side_km)
    chunk_area_sqm = get_chunk_area_sqm(resolved_cell_side_km)
    cell_side_meters = resolved_cell_side_km * 1000.0
    bbox = get_bbox(area_points)
    latitude_step = meters_to_latitude_delta(cell_side_meters)

    zones = []
    sequence = 0
    current_lat = bbox["min_lat"]

    while current_lat < bbox["max_lat"] - 1e-12:
        next_lat = current_lat + latitude_step
        row_center_lat = current_lat + (latitude_step / 2.0)
        longitude_step = meters_to_longitude_delta(cell_side_meters, row_center_lat)
        current_lng = bbox["min_lng"]

        while current_lng < bbox["max_lng"] - 1e-12:
            next_lng = current_lng + longitude_step
            zone_points = build_square_points(current_lng, current_lat, next_lng, next_lat)

            if polygon_intersects_cell(area_points, zone_points):
                zone_geometry = {
                    "type": "Polygon",
                    "coordinates": [[*zone_points, zone_points[0]]],
                }
                zone_area_sqm = polygon_area_sqm(zone_geometry["coordinates"][0])
                zones.append(
                    {
                        "zone_id": f"zone-{sequence}",
                        "geometry": zone_geometry,
                        "points": zone_points,
                        "center": calculate_center(zone_points),
                        "area_sqm": round(zone_area_sqm, 2),
                        "area_hectares": round(zone_area_sqm / 10000, 4),
                        "sequence": sequence,
                    }
                )
                sequence += 1

            current_lng = next_lng

        current_lat = next_lat

    if not zones:
        zone_points = build_zone_square(area_points, area_center, max(total_area_sqm, chunk_area_sqm))
        zone_geometry = {
            "type": "Polygon",
            "coordinates": [[*zone_points, zone_points[0]]],
        }
        zone_area_sqm = polygon_area_sqm(zone_geometry["coordinates"][0])
        zones.append(
            {
                "zone_id": "zone-0",
                "geometry": zone_geometry,
                "points": zone_points,
                "center": area_center,
                "area_sqm": round(zone_area_sqm, 2),
                "area_hectares": round(zone_area_sqm / 10000, 4),
                "sequence": 0,
            }
        )

    zone_count = len(zones)

    area_geometry = {
        "type": "Feature",
        "properties": {},
        "geometry": deepcopy(area_feature.get("geometry", {})),
    }
    area_geometry.setdefault("properties", {})
    area_geometry["properties"].update(
        {
            "center": area_center,
            "area_sqm": round(total_area_sqm, 2),
            "area_hectares": round(total_area_sqm / 10000, 4),
            "cell_side_km": round(resolved_cell_side_km, 4),
        }
    )

    return {
        "area": {
            "geometry": area_geometry,
            "points": area_points,
            "center": area_center,
            "area_sqm": total_area_sqm,
            "area_hectares": total_area_sqm / 10000,
            "chunk_area_sqm": chunk_area_sqm,
            "cell_side_km": resolved_cell_side_km,
            "zone_count": zone_count,
        },
        "zones": zones,
    }


def build_rule_based_zone_metrics(index, coords):
    if coords:
        first_longitude, first_latitude = coords[0]
    else:
        first_longitude, first_latitude = (0.0, 0.0)

    seed = int((index * 7) + math.floor(first_latitude * 100) + math.floor(first_longitude * 100))
    crop_id = RULE_BASED_CROP_IDS[abs(seed) % len(RULE_BASED_CROP_IDS)]
    crop_metadata = RULE_BASED_PRODUCTS[crop_id]

    match_percent = 60 + (abs(seed) % 35)
    criteria = [
        {"name": "دما", "value": 55 + (abs(seed + 11) % 40)},
        {"name": "بارش", "value": 55 + (abs(seed + 17) % 40)},
        {"name": "خاک", "value": 55 + (abs(seed + 23) % 40)},
        {"name": "آب", "value": 55 + (abs(seed + 29) % 40)},
    ]
    soil_quality_score = criteria[2]["value"]
    soil_level = _pick_level(soil_quality_score, 65, 85)
    cultivation_risk_score = max(1, min(100, round(100 - match_percent + ((abs(seed) % 9) - 4))))
    cultivation_risk_level = "low" if cultivation_risk_score <= 30 else "medium" if cultivation_risk_score <= 60 else "high"

    return {
        "soil_quality_score": soil_quality_score,
        "soil_level": soil_level,
        "water_need_level": crop_metadata["water_need_level"],
        "water_need_value": crop_metadata["water_need"],
        "cultivation_risk_level": cultivation_risk_level,
        "recommended_crop": crop_id,
        "match_percent": match_percent,
        "estimated_profit": crop_metadata["estimated_profit"],
        "reason": crop_metadata["reason"],
        "criteria": criteria,
        "algorithm": RULE_BASED_ALGORITHM,
    }


def build_initial_zone_payload(zone):
    recommendation = getattr(zone, "recommendation", None)
    return {
        "zoneId": zone.zone_id,
        "geometry": zone.geometry,
        "crop": recommendation.product.product_id if recommendation else "",
        "matchPercent": recommendation.match_percent if recommendation else 0,
        "waterNeed": recommendation.water_need if recommendation else "",
        "estimatedProfit": recommendation.estimated_profit if recommendation else "",
    }


def build_area_zone_payload(zone):
    base_payload = _build_area_layer_zone_base_payload(zone)
    recommendation = getattr(zone, "recommendation", None)
    water_need_layer = getattr(zone, "water_need_layer", None)
    soil_quality_layer = getattr(zone, "soil_quality_layer", None)
    cultivation_risk_layer = getattr(zone, "cultivation_risk_layer", None)
    base_payload.update(
        {
            "crop": recommendation.product.product_id if recommendation else "",
            "matchPercent": recommendation.match_percent if recommendation else 0,
            "waterNeed": recommendation.water_need if recommendation else "",
            "estimatedProfit": recommendation.estimated_profit if recommendation else "",
            "waterNeedLayer": {
                "level": getattr(water_need_layer, "level", ""),
                "value": getattr(water_need_layer, "value", ""),
                "color": getattr(water_need_layer, "color", ""),
            },
            "soilQualityLayer": {
                "level": getattr(soil_quality_layer, "level", ""),
                "score": getattr(soil_quality_layer, "score", 0),
                "color": getattr(soil_quality_layer, "color", ""),
            },
            "cultivationRiskLayer": {
                "level": getattr(cultivation_risk_layer, "level", ""),
                "color": getattr(cultivation_risk_layer, "color", ""),
            },
        }
    )
    return base_payload


def _serialize_cluster_candidate(candidate_payload):
    if not isinstance(candidate_payload, dict):
        return None

    return {
        "plantId": candidate_payload.get("plant_id"),
        "plantName": str(candidate_payload.get("plant_name") or ""),
        "position": candidate_payload.get("position"),
        "stage": str(candidate_payload.get("stage") or ""),
        "score": candidate_payload.get("score"),
        "predictedYield": candidate_payload.get("predicted_yield"),
        "predictedYieldTons": candidate_payload.get("predicted_yield_tons"),
        "biomass": candidate_payload.get("biomass"),
        "maxLai": candidate_payload.get("max_lai"),
        "simulationEngine": candidate_payload.get("simulation_engine"),
        "simulationModelName": candidate_payload.get("simulation_model_name"),
        "simulationWarning": str(candidate_payload.get("simulation_warning") or ""),
        "supportingMetrics": deepcopy(candidate_payload.get("supporting_metrics") or {}),
    }


def _get_zone_ai_cluster_payload(zone):
    analysis = getattr(zone, "analysis", None)
    raw_response = getattr(analysis, "raw_response", None)
    if not isinstance(raw_response, dict):
        return {}

    cluster_payload = raw_response.get("cluster_recommendation") or {}
    if isinstance(cluster_payload, dict):
        return cluster_payload
    return {}


def _build_zone_cluster_info(zone, cluster_payload):
    cluster_block = cluster_payload.get("cluster_block") or {}
    return {
        "blockCode": str(cluster_payload.get("block_code") or ""),
        "clusterUuid": str(cluster_payload.get("cluster_uuid") or cluster_block.get("uuid") or zone.zone_id),
        "subBlockCode": str(cluster_payload.get("sub_block_code") or cluster_block.get("sub_block_code") or zone.zone_id),
        "clusterLabel": cluster_payload.get("cluster_label"),
        "cellCount": cluster_block.get("cell_count"),
        "cellCodes": deepcopy(cluster_block.get("cell_codes") or []),
        "centerCellCode": cluster_block.get("center_cell_code"),
        "centerCellLat": cluster_block.get("center_cell_lat"),
        "centerCellLon": cluster_block.get("center_cell_lon"),
        "sourceMetadata": deepcopy(cluster_payload.get("source_metadata") or {}),
    }


def _build_zone_cluster_metrics(cluster_payload):
    if not cluster_payload:
        return {
            "satelliteMetrics": {},
            "sensorMetrics": {},
            "resolvedMetrics": {},
            "criteria": [],
        }

    suggested_plant = cluster_payload.get("suggested_plant")
    return {
        "satelliteMetrics": deepcopy(cluster_payload.get("satellite_metrics") or {}),
        "sensorMetrics": deepcopy(cluster_payload.get("sensor_metrics") or {}),
        "resolvedMetrics": deepcopy(cluster_payload.get("resolved_metrics") or {}),
        "criteria": _build_metric_criteria(cluster_payload, suggested_plant),
    }


def _build_zone_crop_prediction(cluster_payload):
    if not cluster_payload:
        return {"suggestedPlant": None, "candidatePlants": []}

    return {
        "suggestedPlant": _serialize_cluster_candidate(cluster_payload.get("suggested_plant")),
        "candidatePlants": [
            item
            for item in (
                _serialize_cluster_candidate(candidate_payload)
                for candidate_payload in (cluster_payload.get("candidate_plants") or [])
            )
            if item is not None
        ],
    }


def _attach_ai_zone_payload(base_payload, zone):
    cluster_payload = _get_zone_ai_cluster_payload(zone)
    base_payload["clusterInfo"] = _build_zone_cluster_info(zone, cluster_payload)
    base_payload["clusterMetrics"] = _build_zone_cluster_metrics(cluster_payload)
    base_payload["cropPrediction"] = _build_zone_crop_prediction(cluster_payload)
    return base_payload


def _build_area_layer_zone_base_payload(zone):
    return _attach_ai_zone_payload(
        {
        "zoneId": zone.zone_id,
        "zoneUuid": str(zone.uuid),
        "geometry": zone.geometry,
        "center": zone.center,
        "area_sqm": zone.area_sqm,
        "area_hectares": zone.area_hectares,
        "sequence": zone.sequence,
        "processing_status": zone.processing_status,
        "processing_error": zone.processing_error,
        },
        zone,
    )


def build_water_need_area_zone_payload(zone):
    base_payload = _build_area_layer_zone_base_payload(zone)
    water_need_layer = getattr(zone, "water_need_layer", None)
    base_payload["waterNeedLayer"] = {
        "level": getattr(water_need_layer, "level", ""),
        "value": getattr(water_need_layer, "value", ""),
        "color": getattr(water_need_layer, "color", ""),
    }
    return base_payload


def build_soil_quality_area_zone_payload(zone):
    base_payload = _build_area_layer_zone_base_payload(zone)
    soil_quality_layer = getattr(zone, "soil_quality_layer", None)
    base_payload["soilQualityLayer"] = {
        "level": getattr(soil_quality_layer, "level", ""),
        "score": getattr(soil_quality_layer, "score", 0),
        "color": getattr(soil_quality_layer, "color", ""),
    }
    return base_payload


def build_cultivation_risk_area_zone_payload(zone):
    base_payload = _build_area_layer_zone_base_payload(zone)
    cultivation_risk_layer = getattr(zone, "cultivation_risk_layer", None)
    base_payload["cultivationRiskLayer"] = {
        "level": getattr(cultivation_risk_layer, "level", ""),
        "color": getattr(cultivation_risk_layer, "color", ""),
    }
    return base_payload


def persist_zone_analysis_metrics(zone, metrics):
    ensure_products_exist()
    product = CropProduct.objects.get(product_id=metrics["recommended_crop"])
    recommendation, _ = CropZoneRecommendation.objects.update_or_create(
        crop_zone=zone,
        defaults={
            "product": product,
            "match_percent": metrics["match_percent"],
            "water_need": metrics["water_need_value"],
            "estimated_profit": metrics["estimated_profit"],
            "reason": metrics["reason"],
        },
    )
    CropZoneCriteria.objects.filter(recommendation=recommendation).delete()
    CropZoneCriteria.objects.bulk_create(
        [
            CropZoneCriteria(
                recommendation=recommendation,
                name=item["name"],
                value=item["value"],
                sequence=index,
            )
            for index, item in enumerate(metrics["criteria"])
        ]
    )
    CropZoneWaterNeedLayer.objects.update_or_create(
        crop_zone=zone,
        defaults={
            "level": metrics["water_need_level"],
            "value": metrics["water_need_value"],
            "color": _get_level_color_map("water", metrics["water_need_level"]),
        },
    )
    CropZoneSoilQualityLayer.objects.update_or_create(
        crop_zone=zone,
        defaults={
            "level": metrics["soil_level"],
            "score": metrics["soil_quality_score"],
            "color": _get_level_color_map("soil", metrics["soil_level"]),
        },
    )
    CropZoneCultivationRiskLayer.objects.update_or_create(
        crop_zone=zone,
        defaults={
            "level": metrics["cultivation_risk_level"],
            "color": _get_level_color_map("risk", metrics["cultivation_risk_level"]),
        },
    )
    return recommendation


def ensure_rule_based_zone_data(zone, force=False):
    has_recommendation = CropZoneRecommendation.objects.filter(crop_zone=zone).exists()
    if has_recommendation and not force:
        return zone

    metrics = build_rule_based_zone_metrics(zone.sequence, zone.points)
    persist_zone_analysis_metrics(zone, metrics)
    return zone


def _get_level_color_map(layer_name, level):
    mappings = {
        "water": {"low": "#7dd3fc", "medium": "#0ea5e9", "high": "#0369a1"},
        "soil": {"low": "#ef4444", "medium": "#eab308", "high": "#22c55e"},
        "risk": {"low": "#22c55e", "medium": "#f59e0b", "high": "#ef4444"},
    }
    return mappings[layer_name][level]


def _pick_level(score, low_threshold, high_threshold):
    if score >= high_threshold:
        return "high"
    if score >= low_threshold:
        return "medium"
    return "low"


def _format_range(start, end, suffix):
    return f"{start}-{end} {suffix}"


def _derive_analysis_metrics(depths):
    if not depths:
        return {
            "soil_quality_score": 0,
            "soil_level": "low",
            "water_need_level": "high",
            "water_need_value": "0-0 m³/ha",
            "cultivation_risk_level": "high",
            "recommended_crop": PRODUCT_DEFAULTS[0]["id"],
            "match_percent": 0,
            "estimated_profit": "0-0 میلیون/هکتار",
            "reason": "داده تحلیل خاک موجود نیست",
            "criteria": [],
        }

    avg_ph = sum(item.get("phh2o", 0) for item in depths) / len(depths)
    avg_soc = sum(item.get("soc", 0) for item in depths) / len(depths)
    avg_clay = sum(item.get("clay", 0) for item in depths) / len(depths)
    avg_nitrogen = sum(item.get("nitrogen", 0) for item in depths) / len(depths)
    avg_wv0033 = sum(item.get("wv0033", 0) for item in depths) / len(depths)

    soil_quality_score = max(0, min(100, round((avg_soc * 20) + (avg_nitrogen * 120) + (avg_wv0033 * 120) + (20 - abs(avg_ph - 7) * 10))))
    soil_level = _pick_level(soil_quality_score, 50, 80)

    water_base = round(3000 + (avg_clay * 70))
    water_need_value = _format_range(water_base, water_base + 1000, "m³/ha")
    water_need_level = "low" if water_base < 4000 else "medium" if water_base < 5000 else "high"

    cultivation_risk_score = max(0, min(100, round(100 - soil_quality_score + abs(avg_ph - 7) * 8)))
    cultivation_risk_level = "low" if cultivation_risk_score <= 30 else "medium" if cultivation_risk_score <= 55 else "high"

    if water_need_level == "low" and soil_quality_score >= 85:
        recommended_crop = "saffron"
        estimated_profit = "۵۰-۱۵۰ میلیون/هکتار"
    elif soil_quality_score >= 70:
        recommended_crop = "wheat"
        estimated_profit = "۱۵-۲۵ میلیون/هکتار"
    else:
        recommended_crop = "canola"
        estimated_profit = "۲۰-۳۵ میلیون/هکتار"

    match_percent = max(1, min(100, round((soil_quality_score * 0.55) + ((100 - cultivation_risk_score) * 0.45))))
    reason = "خاک و شرایط رطوبتی این زون برای محصول پیشنهادی مناسب ارزیابی شده است"
    criteria = [
        {"name": "دما", "value": max(1, min(100, round(70 + (avg_ph - 6.5) * 10)))},
        {"name": "بارش", "value": max(1, min(100, round(60 + avg_wv0033 * 100)))},
        {"name": "خاک", "value": soil_quality_score},
        {"name": "آب", "value": max(1, min(100, round(100 - ((water_base - 3000) / 30))))},
    ]

    return {
        "soil_quality_score": soil_quality_score,
        "soil_level": soil_level,
        "water_need_level": water_need_level,
        "water_need_value": water_need_value,
        "cultivation_risk_level": cultivation_risk_level,
        "recommended_crop": recommended_crop,
        "match_percent": match_percent,
        "estimated_profit": estimated_profit,
        "reason": reason,
        "criteria": criteria,
    }


def fetch_soil_data_for_zone(zone):
    center = zone.center or calculate_center(zone.points)
    payload = {
        "lon": center["longitude"],
        "lat": center["latitude"],
        "zone": {
            "id": zone.zone_id,
            "geometry": zone.geometry,
            "center": center,
            "area_sqm": zone.area_sqm,
            "area_hectares": zone.area_hectares,
        },
    }
    return external_request("ai", "/soil-data", method="POST", payload=payload).data


def analyze_and_store_zone_soil_data(zone_id):
    ensure_products_exist()
    zone = CropZone.objects.select_related("crop_area").get(id=zone_id)
    if zone.processing_status == CropZone.STATUS_COMPLETED:
        return zone

    zone.processing_status = CropZone.STATUS_PROCESSING
    zone.processing_error = ""
    zone.save(update_fields=["processing_status", "processing_error", "updated_at"])

    try:
        adapter_data = fetch_soil_data_for_zone(zone)
        soil_data = adapter_data.get("data", {}) if isinstance(adapter_data, dict) else {}
        depths = soil_data.get("depths", [])
        metrics = _derive_analysis_metrics(depths)
        product = CropProduct.objects.get(product_id=metrics["recommended_crop"])

        CropZoneAnalysis.objects.update_or_create(
            crop_zone=zone,
            defaults={
                "source": soil_data.get("source", ""),
                "external_record_id": str(soil_data.get("id", "")),
                "longitude": Decimal(str(soil_data.get("lon", zone.center.get("longitude", 0)))),
                "latitude": Decimal(str(soil_data.get("lat", zone.center.get("latitude", 0)))),
                "raw_response": adapter_data if isinstance(adapter_data, dict) else {},
                "depths": depths,
            },
        )
        persist_zone_analysis_metrics(zone, metrics)
        zone.processing_status = CropZone.STATUS_COMPLETED
        zone.processing_error = ""
        zone.save(update_fields=["processing_status", "processing_error", "updated_at"])
    except Exception as exc:
        zone.processing_status = CropZone.STATUS_FAILED
        zone.processing_error = str(exc)
        zone.save(update_fields=["processing_status", "processing_error", "updated_at"])
        raise

    return zone


def _get_stale_zone_ids(zones):
    completed_task_ids = {
        zone.task_id
        for zone in zones
        if zone.processing_status == CropZone.STATUS_COMPLETED and zone.task_id
    }
    stale_before = timezone.now() - timedelta(seconds=get_task_stale_seconds())
    stale_zone_ids = []

    for zone in zones:
        if zone.processing_status == CropZone.STATUS_COMPLETED or not zone.task_id:
            continue
        if zone.task_id in completed_task_ids:
            stale_zone_ids.append(zone.id)
            continue
        if zone.updated_at > stale_before:
            continue

        try:
            task_state = AsyncResult(zone.task_id).state
        except Exception:
            task_state = TASK_STATE_PENDING

        if task_state in {
            TASK_STATE_PENDING,
            TASK_STATE_SUCCESS,
            TASK_STATE_FAILURE,
            TASK_STATE_REVOKED,
        }:
            stale_zone_ids.append(zone.id)

    return stale_zone_ids


def dispatch_zone_processing_tasks(crop_area_id=None, zone_ids=None, force=False):
    from .tasks import process_zone_soil_data

    queryset = CropZone.objects.all()
    if crop_area_id is not None:
        queryset = queryset.filter(crop_area_id=crop_area_id)
    if zone_ids is not None:
        queryset = queryset.filter(id__in=zone_ids)

    zones = list(queryset.only("id", "task_id", "processing_status").order_by("sequence", "id"))
    for zone in zones:
        if zone.processing_status == CropZone.STATUS_COMPLETED:
            continue
        if not force and zone.processing_status == CropZone.STATUS_PROCESSING and zone.task_id:
            continue
        if not force and zone.processing_status == CropZone.STATUS_PENDING and zone.task_id:
            continue

        try:
            async_result = process_zone_soil_data.delay(zone.id)
            task_identifier = getattr(async_result, "id", "") or str(uuid.uuid4())
            processing_error = ""
        except OperationalError as exc:
            task_identifier = str(uuid.uuid4())
            processing_error = f"Celery broker unavailable: {exc}"
        except Exception as exc:
            task_identifier = str(uuid.uuid4())
            processing_error = f"Celery dispatch failed: {exc}"

        update_fields = {
            "task_id": task_identifier,
            "processing_status": CropZone.STATUS_PENDING,
        }
        update_fields["processing_error"] = processing_error
        CropZone.objects.filter(id=zone.id).update(**update_fields)


def create_missing_zones_for_area(crop_area):
    if crop_area.zones.exists():
        return list(crop_area.zones.order_by("sequence", "id"))

    area_feature = normalize_area_feature(crop_area.geometry)
    zoning_result = split_area_into_zones(
        area_feature,
        cell_side_km=math.sqrt(max(crop_area.chunk_area_sqm, 1)) / 1000.0,
    )
    zones = CropZone.objects.bulk_create(
        [
            CropZone(
                crop_area=crop_area,
                zone_id=zone["zone_id"],
                geometry=zone["geometry"],
                points=zone["points"],
                center=zone["center"],
                area_sqm=round(zone["area_sqm"], 2),
                area_hectares=round(zone["area_hectares"], 4),
                sequence=zone["sequence"],
            )
            for zone in zoning_result["zones"]
        ]
    )
    crop_area.zone_count = len(zones)
    crop_area.save(update_fields=["zone_count", "updated_at"])
    return list(crop_area.zones.order_by("sequence", "id"))


def get_farm_for_uuid(farm_uuid, owner=None):
    if not farm_uuid:
        raise ValueError("farm_uuid is required.")

    filters = {"farm_uuid": farm_uuid}
    if owner is not None:
        filters["owner"] = owner

    try:
        return FarmHub.objects.get(**filters)
    except FarmHub.DoesNotExist as exc:
        raise ValueError("Farm not found.") from exc


def _raise_ai_response_error(response, default_message):
    payload = response.data if isinstance(response.data, dict) else {}
    message = payload.get("msg") or payload.get("message") or default_message
    if response.status_code >= 500:
        raise ImproperlyConfigured(message)
    raise ValueError(message)


def _unwrap_ai_response(response, *, expected_statuses):
    if response.status_code not in expected_statuses:
        _raise_ai_response_error(response, f"AI location_data API returned status {response.status_code}.")

    payload = response.data if isinstance(response.data, dict) else {}
    if "data" in payload:
        return payload["data"]
    return payload


def _request_ai_location_data(path, *, method="GET", payload=None, query=None):
    return external_request(
        "ai",
        path,
        method=method,
        payload=payload,
        query=query,
    )


def _feature_from_geometry(geometry):
    if not isinstance(geometry, dict):
        return get_default_area_feature()
    if geometry.get("type") == "Feature":
        return normalize_area_feature(geometry)
    return normalize_area_feature(
        {
            "type": "Feature",
            "properties": {},
            "geometry": geometry,
        }
    )


def _upsert_crop_area_snapshot(farm, area_feature):
    normalized_feature = normalize_area_feature(area_feature)
    ring = get_polygon_ring(normalized_feature)
    points = normalize_points(ring)
    area_sqm = round(polygon_area_sqm(ring), 2)
    area_hectares = round(area_sqm / 10000.0, 4)
    defaults = {
        "geometry": normalized_feature,
        "points": points,
        "center": calculate_center(points),
        "area_sqm": area_sqm,
        "area_hectares": area_hectares,
        "chunk_area_sqm": round(get_chunk_area_sqm(), 2),
    }

    crop_area = farm.current_crop_area
    if crop_area is None:
        crop_area = CropArea.objects.create(
            farm=farm,
            zone_count=0,
            **defaults,
        )
        farm.current_crop_area = crop_area
        farm.save(update_fields=["current_crop_area", "updated_at"])
        return crop_area

    for field_name, value in defaults.items():
        setattr(crop_area, field_name, value)
    crop_area.save(update_fields=[*defaults.keys(), "updated_at"])
    return crop_area


def _get_farm_area_feature(farm, fallback=None):
    if fallback is not None:
        return normalize_area_feature(fallback)

    crop_area = farm.current_crop_area or farm.crop_areas.order_by("-created_at", "-id").first()
    if crop_area is not None and crop_area.geometry:
        return normalize_area_feature(crop_area.geometry)

    return get_default_area_feature()


def _build_processing_layer_payload(farm, remote_payload, *, page, page_size):
    area_feature = _get_farm_area_feature(
        farm,
        fallback=((remote_payload.get("location") or {}).get("farm_boundary")),
    )
    location = remote_payload.get("location") or {}
    run = remote_payload.get("run") or {}
    status_value = str(remote_payload.get("status") or "").lower()
    task_status = "PROCESSING" if status_value == "processing" else "PENDING"

    return {
        "task": {
            "status": task_status,
            "stage": status_value or "queued",
            "stage_label": "در حال دریافت تقسیم بندی و متریک ها از AI",
            "area_uuid": str(getattr(farm.current_crop_area, "uuid", "")) if farm.current_crop_area_id else "",
            "total_zones": 0,
            "completed_zones": 0,
            "processing_zones": 0,
            "pending_zones": 0,
            "failed_zones": 0,
            "remaining_zones": 0,
            "progress_percent": 0,
            "summary": {
                "done": 0,
                "in_progress": 0,
                "remaining": 0,
                "failed": 0,
            },
            "message": "تقسیم بندی و متریک های کشت در AI در حال آماده سازی است.",
            "failed_zone_errors": [],
            "cell_side_km": round(get_default_cell_side_km(), 4),
            "task_id": remote_payload.get("task_id") or (run.get("metadata") or {}).get("task_id"),
        },
        "area": area_feature,
        "zones": [],
        "location": location,
        "farmerBlocks": deepcopy(((location.get("block_layout") or {}).get("blocks") or [])),
        "clusterBlocks": [],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
            "total_zones": 0,
            "returned_zones": 0,
            "has_next": False,
            "has_previous": False,
        },
    }


def _hash_color(value):
    digest = hashlib.md5(str(value).encode("utf-8")).hexdigest()
    return f"#{digest[:6]}"


def _clamp_percent(value, *, default=0):
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default
    return max(0, min(100, round(numeric)))


def _extract_zone_points(geometry):
    coordinates = (geometry or {}).get("coordinates") or []
    if not coordinates or not coordinates[0]:
        return []
    ring = coordinates[0]
    return ring[:-1] if len(ring) > 1 and ring[0] == ring[-1] else ring


def _build_metric_criteria(cluster_payload, suggested_plant):
    resolved_metrics = cluster_payload.get("resolved_metrics") or {}
    criteria = []

    ndvi_score = _clamp_percent((resolved_metrics.get("ndvi") or 0) * 100)
    criteria.append({"name": "NDVI", "value": ndvi_score})

    ndwi_raw = resolved_metrics.get("ndwi")
    ndwi_score = _clamp_percent(((float(ndwi_raw) + 1.0) / 2.0) * 100) if ndwi_raw is not None else 0
    criteria.append({"name": "NDWI", "value": ndwi_score})

    soil_moisture = resolved_metrics.get("soil_moisture")
    if soil_moisture is not None:
        criteria.append({"name": "رطوبت خاک", "value": _clamp_percent(soil_moisture)})

    nitrogen = resolved_metrics.get("nitrogen")
    if nitrogen is not None:
        criteria.append({"name": "نیتروژن", "value": _clamp_percent(float(nitrogen) * 4)})

    if suggested_plant is not None:
        criteria.append({"name": "امتیاز AI", "value": _clamp_percent(suggested_plant.get("score"))})

    return criteria[:4]


def _derive_layer_bundle(cluster_payload, suggested_plant):
    resolved_metrics = cluster_payload.get("resolved_metrics") or {}
    criteria = _build_metric_criteria(cluster_payload, suggested_plant)
    soil_score = next((item["value"] for item in criteria if item["name"] in {"NDVI", "نیتروژن"}), 0)
    if soil_score >= 75:
        soil_level = "high"
    elif soil_score >= 45:
        soil_level = "medium"
    else:
        soil_level = "low"

    moisture_value = resolved_metrics.get("soil_moisture")
    ndwi_raw = resolved_metrics.get("ndwi")
    if moisture_value is not None:
        water_score = _clamp_percent(100 - float(moisture_value))
        water_value_text = f"{round(float(moisture_value), 2)}% soil moisture"
    elif ndwi_raw is not None:
        water_score = _clamp_percent(100 - (((float(ndwi_raw) + 1.0) / 2.0) * 100))
        water_value_text = f"NDWI {round(float(ndwi_raw), 3)}"
    else:
        water_score = 0
        water_value_text = ""
    if water_score >= 65:
        water_level = "high"
    elif water_score >= 35:
        water_level = "medium"
    else:
        water_level = "low"

    ai_score = _clamp_percent((suggested_plant or {}).get("score"))
    risk_score = max(0, min(100, round((100 - soil_score) * 0.6 + (100 - ai_score) * 0.4)))
    if risk_score >= 65:
        risk_level = "high"
    elif risk_score >= 35:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "criteria": criteria,
        "soil": {
            "score": soil_score,
            "level": soil_level,
            "color": _get_level_color_map("soil", soil_level),
        },
        "water": {
            "level": water_level,
            "value": water_value_text,
            "color": _get_level_color_map("water", water_level),
        },
        "risk": {
            "level": risk_level,
            "color": _get_level_color_map("risk", risk_level),
        },
    }


def _sync_crop_area_from_ai(farm, remote_payload, recommendation_payload=None):
    location_payload = remote_payload.get("location") or {}
    area_feature = _get_farm_area_feature(
        farm,
        fallback=location_payload.get("farm_boundary"),
    )
    crop_area = _upsert_crop_area_snapshot(farm, area_feature)
    subdivision_result = remote_payload.get("subdivision_result") or {}
    cluster_blocks = subdivision_result.get("cluster_blocks") or []
    recommendation_map = {}
    for cluster in (recommendation_payload or {}).get("clusters", []):
        cluster_uuid = str(cluster.get("cluster_uuid") or ((cluster.get("cluster_block") or {}).get("uuid") or ""))
        if cluster_uuid:
            recommendation_map[cluster_uuid] = cluster

    existing_zones = {zone.zone_id: zone for zone in crop_area.zones.all()}
    retained_zone_ids = []

    with transaction.atomic():
        for sequence, cluster_block in enumerate(
            sorted(cluster_blocks, key=lambda item: (item.get("cluster_label") is None, item.get("cluster_label"), item.get("sub_block_code") or ""))
        ):
            zone_id = str(cluster_block.get("uuid") or cluster_block.get("sub_block_code") or f"cluster-{sequence}")
            geometry = cluster_block.get("geometry") or {}
            points = _extract_zone_points(geometry)
            area_sqm = round(polygon_area_sqm((geometry.get("coordinates") or [[points]])[0]), 2) if geometry.get("coordinates") else 0.0
            area_hectares = round(area_sqm / 10000.0, 4)
            zone_defaults = {
                "geometry": geometry,
                "points": points,
                "center": {
                    "longitude": float(cluster_block.get("centroid_lon") or 0),
                    "latitude": float(cluster_block.get("centroid_lat") or 0),
                },
                "area_sqm": area_sqm,
                "area_hectares": area_hectares,
                "sequence": sequence,
                "processing_status": CropZone.STATUS_COMPLETED,
                "processing_error": "",
                "task_id": str(((remote_payload.get("run") or {}).get("metadata") or {}).get("task_id") or ""),
            }
            zone = existing_zones.get(zone_id)
            if zone is None:
                zone = CropZone.objects.create(crop_area=crop_area, zone_id=zone_id, **zone_defaults)
            else:
                for field_name, value in zone_defaults.items():
                    setattr(zone, field_name, value)
                zone.save(update_fields=[*zone_defaults.keys(), "updated_at"])
            retained_zone_ids.append(zone.zone_id)

            cluster_payload = recommendation_map.get(zone_id, {})
            suggested_plant = cluster_payload.get("suggested_plant")
            layer_bundle = _derive_layer_bundle(cluster_payload, suggested_plant)

            product_id = str((suggested_plant or {}).get("plant_name") or (suggested_plant or {}).get("plant_id") or "")
            if product_id:
                product, _ = CropProduct.objects.update_or_create(
                    product_id=product_id,
                    defaults={
                        "label": str((suggested_plant or {}).get("plant_name") or product_id),
                        "color": _hash_color(product_id),
                    },
                )
                recommendation, _ = CropZoneRecommendation.objects.update_or_create(
                    crop_zone=zone,
                    defaults={
                        "product": product,
                        "match_percent": _clamp_percent((suggested_plant or {}).get("score")),
                        "water_need": layer_bundle["water"]["value"],
                        "estimated_profit": (
                            f"{round(float((suggested_plant or {}).get('predicted_yield_tons')), 2)} ton/ha"
                            if (suggested_plant or {}).get("predicted_yield_tons") is not None
                            else ""
                        ),
                        "reason": "پیشنهاد محصول بر اساس متریک های سنجش از دور و تحلیل کلاستر AI تولید شده است.",
                    },
                )
                CropZoneCriteria.objects.filter(recommendation=recommendation).delete()
                CropZoneCriteria.objects.bulk_create(
                    [
                        CropZoneCriteria(
                            recommendation=recommendation,
                            name=item["name"],
                            value=item["value"],
                            sequence=index,
                        )
                        for index, item in enumerate(layer_bundle["criteria"])
                    ]
                )
            else:
                CropZoneRecommendation.objects.filter(crop_zone=zone).delete()

            CropZoneWaterNeedLayer.objects.update_or_create(
                crop_zone=zone,
                defaults=layer_bundle["water"],
            )
            CropZoneSoilQualityLayer.objects.update_or_create(
                crop_zone=zone,
                defaults=layer_bundle["soil"],
            )
            CropZoneCultivationRiskLayer.objects.update_or_create(
                crop_zone=zone,
                defaults=layer_bundle["risk"],
            )
            CropZoneAnalysis.objects.update_or_create(
                crop_zone=zone,
                defaults={
                    "source": "ai_location_data",
                    "external_record_id": zone_id,
                    "latitude": zone.center.get("latitude"),
                    "longitude": zone.center.get("longitude"),
                    "raw_response": {
                        "remote_sensing": remote_payload,
                        "cluster_recommendation": cluster_payload,
                    },
                    "depths": [],
                },
            )

        CropZone.objects.filter(crop_area=crop_area).exclude(zone_id__in=retained_zone_ids).delete()
        crop_area.zone_count = len(retained_zone_ids)
        crop_area.chunk_area_sqm = subdivision_result.get("chunk_size_sqm") or crop_area.chunk_area_sqm
        crop_area.save(update_fields=["zone_count", "chunk_area_sqm", "updated_at"])

    return crop_area


def _get_ai_remote_sensing_payload(*, farm_uuid, page, page_size):
    response = _request_ai_location_data(
        AI_REMOTE_SENSING_PATH,
        method="GET",
        query={
            "farm_uuid": str(farm_uuid),
            "page": page,
            "page_size": page_size,
        },
    )
    return _unwrap_ai_response(response, expected_statuses={200})


def _start_ai_remote_sensing(*, farm_uuid):
    response = _request_ai_location_data(
        AI_REMOTE_SENSING_PATH,
        method="POST",
        payload={"farm_uuid": str(farm_uuid)},
    )
    return _unwrap_ai_response(response, expected_statuses={202})


def _get_ai_cluster_recommendations(*, farm_uuid):
    response = _request_ai_location_data(
        AI_CLUSTER_RECOMMENDATIONS_PATH,
        method="GET",
        query={"farm_uuid": str(farm_uuid)},
    )
    return _unwrap_ai_response(response, expected_statuses={200})


def _build_ai_layer_context(remote_payload, recommendation_payload=None):
    location = deepcopy(remote_payload.get("location") or {})
    subdivision_result = deepcopy(remote_payload.get("subdivision_result") or {})
    run = deepcopy(remote_payload.get("run") or {})
    return {
        "source": {
            "type": "ai_location_data",
            "service": "ai",
            "status": str(remote_payload.get("status") or ""),
        },
        "location": location,
        "farmerBlocks": deepcopy(((location.get("block_layout") or {}).get("blocks") or [])),
        "clusterBlocks": deepcopy(subdivision_result.get("cluster_blocks") or []),
        "subdivisionSummary": {
            "clusterCount": subdivision_result.get("cluster_count")
            or len(subdivision_result.get("cluster_blocks") or []),
            "chunkSizeSqm": subdivision_result.get("chunk_size_sqm") or remote_payload.get("chunk_size_sqm"),
            "selectedFeatures": deepcopy(
                subdivision_result.get("selected_features")
                or run.get("selected_features")
                or []
            ),
            "temporalExtent": deepcopy(remote_payload.get("temporal_extent") or {}),
            "summary": deepcopy(remote_payload.get("summary") or {}),
        },
        "registeredPlants": deepcopy((recommendation_payload or {}).get("registered_plants") or []),
        "evaluatedPlantCount": (recommendation_payload or {}).get("evaluated_plant_count"),
    }


def _get_latest_layer_payload_from_ai(zone_builder, *, farm_uuid, owner=None, page=1, page_size=DEFAULT_ZONE_PAGE_SIZE):
    farm = get_farm_for_uuid(farm_uuid, owner=owner)
    remote_payload = _get_ai_remote_sensing_payload(
        farm_uuid=farm_uuid,
        page=page,
        page_size=page_size,
    )
    remote_status = str(remote_payload.get("status") or "").lower()
    if remote_status == "not_found":
        remote_payload = _start_ai_remote_sensing(farm_uuid=farm_uuid)
        return _build_processing_layer_payload(farm, remote_payload, page=page, page_size=page_size)
    if remote_status != "success":
        return _build_processing_layer_payload(farm, remote_payload, page=page, page_size=page_size)

    recommendation_payload = None
    try:
        recommendation_payload = _get_ai_cluster_recommendations(farm_uuid=farm_uuid)
    except ValueError:
        recommendation_payload = None

    crop_area = _sync_crop_area_from_ai(farm, remote_payload, recommendation_payload)
    return _build_latest_area_layer_payload(
        zone_builder,
        area=crop_area,
        page=page,
        page_size=page_size,
        extra_payload=_build_ai_layer_context(remote_payload, recommendation_payload),
    )


def ensure_latest_area_ready_for_processing(farm_uuid, area_feature=None, owner=None):
    farm = get_farm_for_uuid(farm_uuid, owner=owner)
    return _upsert_crop_area_snapshot(farm, _get_farm_area_feature(farm, fallback=area_feature))


def create_zones_and_dispatch(area_feature, cell_side_km=None, farm=None):
    if farm is None:
        raise ValueError("farm is required.")

    crop_area = _upsert_crop_area_snapshot(farm, area_feature)
    CropZone.objects.filter(crop_area=crop_area).delete()
    crop_area.zone_count = 0
    crop_area.chunk_area_sqm = round(get_chunk_area_sqm(cell_side_km), 2)
    crop_area.save(update_fields=["zone_count", "chunk_area_sqm", "updated_at"])
    return crop_area, []


def _zones_queryset(zone_ids=None):
    queryset = CropZone.objects.select_related(
        "recommendation__product",
        "water_need_layer",
        "soil_quality_layer",
        "cultivation_risk_layer",
        "analysis",
    ).prefetch_related(
        Prefetch("recommendation__criteria", queryset=CropZoneCriteria.objects.order_by("sequence", "id"))
    ).order_by("sequence", "id")
    if zone_ids:
        queryset = queryset.filter(zone_id__in=zone_ids)
    return queryset


def _get_idle_area_payload(page, page_size):
    return {
        "task": {
            "status": "IDLE",
            "area_uuid": "",
            "total_zones": 0,
            "completed_zones": 0,
            "processing_zones": 0,
            "pending_zones": 0,
            "failed_zones": 0,
            "failed_zone_errors": [],
            "cell_side_km": round(get_default_cell_side_km(), 4),
        },
        "area": get_default_area_feature(),
        "zones": [],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
            "total_zones": 0,
            "returned_zones": 0,
            "has_next": False,
            "has_previous": False,
        },
    }


def _build_latest_area_layer_payload(
    zone_builder,
    area=None,
    page=1,
    page_size=DEFAULT_ZONE_PAGE_SIZE,
    extra_payload=None,
):
    area = area or CropArea.objects.order_by("-created_at", "-id").first()
    if not area:
        return _get_idle_area_payload(page, page_size)

    status_zones = list(area.zones.only("zone_id", "task_id", "processing_status", "processing_error"))
    total_zones = len(status_zones)
    completed_zones = sum(1 for zone in status_zones if zone.processing_status == CropZone.STATUS_COMPLETED)
    processing_zones = sum(1 for zone in status_zones if zone.processing_status == CropZone.STATUS_PROCESSING)
    failed_zones = sum(1 for zone in status_zones if zone.processing_status == CropZone.STATUS_FAILED)
    pending_zones = sum(1 for zone in status_zones if zone.processing_status == CropZone.STATUS_PENDING)
    total_pages = math.ceil(total_zones / page_size) if total_zones else 0
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    zones = list(_zones_queryset().filter(crop_area=area)[start_index:end_index])

    if failed_zones:
        task_status = "FAILURE"
    elif total_zones and completed_zones == total_zones:
        task_status = "SUCCESS"
    elif processing_zones or completed_zones:
        task_status = "PROCESSING"
    else:
        task_status = "PENDING"

    current_stage = "waiting_to_start"
    if failed_zones:
        current_stage = "failed"
    elif total_zones and completed_zones == total_zones:
        current_stage = "completed"
    elif processing_zones:
        current_stage = "processing_zones"
    elif pending_zones and completed_zones:
        current_stage = "continuing_processing"
    elif pending_zones:
        current_stage = "queued"

    progress_percent = 0
    if total_zones:
        progress_percent = round((completed_zones / total_zones) * 100, 2)

    payload = {
        "task": {
            "status": task_status,
            "stage": current_stage,
            "stage_label": {
                "waiting_to_start": "در انتظار شروع پردازش",
                "queued": "تسک ساخته شده و در صف پردازش است",
                "processing_zones": "در حال پردازش زون‌ها",
                "continuing_processing": "بخشی از زون‌ها پردازش شده و بقیه در صف هستند",
                "completed": "پردازش همه زون‌ها کامل شده است",
                "failed": "پردازش بعضی زون‌ها با خطا مواجه شده است",
            }[current_stage],
            "area_uuid": str(area.uuid),
            "total_zones": total_zones,
            "completed_zones": completed_zones,
            "processing_zones": processing_zones,
            "pending_zones": pending_zones,
            "failed_zones": failed_zones,
            "remaining_zones": max(total_zones - completed_zones, 0),
            "progress_percent": progress_percent,
            "summary": {
                "done": completed_zones,
                "in_progress": processing_zones,
                "remaining": pending_zones,
                "failed": failed_zones,
            },
            "message": f"از مجموع {total_zones} زون، {completed_zones} زون پردازش شده، {processing_zones} زون در حال پردازش و {pending_zones} زون باقی مانده است.",
            "failed_zone_errors": [
                {
                    "zoneId": zone.zone_id,
                    "error": zone.processing_error,
                }
                for zone in status_zones
                if zone.processing_status == CropZone.STATUS_FAILED and zone.processing_error
            ],
            "cell_side_km": round(math.sqrt(max(area.chunk_area_sqm, 1)) / 1000.0, 4),
        },
        "area": area.geometry,
        "zones": [zone_builder(zone) for zone in zones],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "total_zones": total_zones,
            "returned_zones": len(zones),
            "has_next": page < total_pages,
            "has_previous": page > 1 and total_pages > 0,
        },
    }
    if extra_payload:
        payload.update(extra_payload)
    return payload


def get_latest_area_payload(*, farm_uuid, owner=None, page=1, page_size=DEFAULT_ZONE_PAGE_SIZE):
    return _get_latest_layer_payload_from_ai(
        build_area_zone_payload,
        farm_uuid=farm_uuid,
        owner=owner,
        page=page,
        page_size=page_size,
    )


def get_latest_water_need_payload(*, farm_uuid, owner=None, page=1, page_size=DEFAULT_ZONE_PAGE_SIZE):
    return _get_latest_layer_payload_from_ai(
        build_water_need_area_zone_payload,
        farm_uuid=farm_uuid,
        owner=owner,
        page=page,
        page_size=page_size,
    )


def get_latest_soil_quality_payload(*, farm_uuid, owner=None, page=1, page_size=DEFAULT_ZONE_PAGE_SIZE):
    return _get_latest_layer_payload_from_ai(
        build_soil_quality_area_zone_payload,
        farm_uuid=farm_uuid,
        owner=owner,
        page=page,
        page_size=page_size,
    )


def get_latest_cultivation_risk_payload(*, farm_uuid, owner=None, page=1, page_size=DEFAULT_ZONE_PAGE_SIZE):
    return _get_latest_layer_payload_from_ai(
        build_cultivation_risk_area_zone_payload,
        farm_uuid=farm_uuid,
        owner=owner,
        page=page,
        page_size=page_size,
    )


def get_initial_zones_payload(crop_area):
    zones = _zones_queryset().filter(crop_area=crop_area)
    return {
        "total_area_hectares": crop_area.area_hectares,
        "total_area_sqm": crop_area.area_sqm,
        "zone_count": crop_area.zone_count,
        "zones": [build_initial_zone_payload(zone) for zone in zones],
    }


def get_water_need_payload(zone_ids=None):
    zones = _zones_queryset(zone_ids)
    return {
        "zones": [
            {
                "zoneId": zone.zone_id,
                "geometry": zone.geometry,
                "level": getattr(zone.water_need_layer, "level", ""),
                "value": getattr(zone.water_need_layer, "value", ""),
                "color": getattr(zone.water_need_layer, "color", ""),
            }
            for zone in zones
        ]
    }


def get_soil_quality_payload(zone_ids=None):
    zones = _zones_queryset(zone_ids)
    return {
        "zones": [
            {
                "zoneId": zone.zone_id,
                "geometry": zone.geometry,
                "level": getattr(zone.soil_quality_layer, "level", ""),
                "score": getattr(zone.soil_quality_layer, "score", 0),
                "color": getattr(zone.soil_quality_layer, "color", ""),
            }
            for zone in zones
        ]
    }


def get_cultivation_risk_payload(zone_ids=None):
    zones = _zones_queryset(zone_ids)
    return {
        "zones": [
            {
                "zoneId": zone.zone_id,
                "geometry": zone.geometry,
                "level": getattr(zone.cultivation_risk_layer, "level", ""),
                "color": getattr(zone.cultivation_risk_layer, "color", ""),
            }
            for zone in zones
        ]
    }


def get_zone_details_payload(zone_id, *, farm_uuid=None, owner=None):
    zone_filters = {"zone_id": zone_id}
    if farm_uuid:
        _get_latest_layer_payload_from_ai(
            build_area_zone_payload,
            farm_uuid=farm_uuid,
            owner=owner,
            page=1,
            page_size=DEFAULT_ZONE_PAGE_SIZE,
        )
        zone_filters["crop_area__farm__farm_uuid"] = farm_uuid
    if owner is not None:
        zone_filters["crop_area__farm__owner"] = owner

    zone = _zones_queryset().get(**zone_filters)
    recommendation = getattr(zone, "recommendation", None)
    criteria = recommendation.criteria.all() if recommendation else []
    cluster_payload = _get_zone_ai_cluster_payload(zone)
    return {
        "zoneId": zone.zone_id,
        "crop": recommendation.product.product_id if recommendation else "",
        "matchPercent": recommendation.match_percent if recommendation else 0,
        "waterNeed": recommendation.water_need if recommendation else "",
        "estimatedProfit": recommendation.estimated_profit if recommendation else "",
        "reason": recommendation.reason if recommendation else "",
        "criteria": [{"name": item.name, "value": item.value} for item in criteria],
        "area_hectares": zone.area_hectares,
        "clusterInfo": _build_zone_cluster_info(zone, cluster_payload),
        "clusterMetrics": _build_zone_cluster_metrics(cluster_payload),
        "cropPrediction": _build_zone_crop_prediction(cluster_payload),
    }
