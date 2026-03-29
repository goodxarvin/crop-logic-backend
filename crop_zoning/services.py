import math
from copy import deepcopy
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import Prefetch

from external_api_adapter.adapter import request as external_request

from .mock_data import AREA_RESPONSE_DATA, PRODUCTS_RESPONSE_DATA
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
PRODUCT_DEFAULTS = PRODUCTS_RESPONSE_DATA["products"]


def get_chunk_area_sqm():
    raw_value = getattr(settings, "CROP_ZONE_CHUNK_AREA_SQM", 0)
    try:
        chunk_area = float(raw_value)
    except (TypeError, ValueError):
        chunk_area = 0
    if chunk_area <= 0:
        raise ValueError("CROP_ZONE_CHUNK_AREA_SQM must be a positive number.")
    return chunk_area


def get_default_area_feature():
    return deepcopy(AREA_RESPONSE_DATA["area"])


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


def build_zone_square(area_points, center, zone_area_sqm):
    if len(area_points) < 4:
        return area_points

    width = math.sqrt(max(zone_area_sqm, 1))
    half_width = width / 2.0

    latitude_factor = 111320.0
    longitude_factor = 111320.0 * math.cos(math.radians(center["latitude"]))
    if longitude_factor == 0:
        longitude_factor = 1.0

    delta_lat = half_width / latitude_factor
    delta_lng = half_width / longitude_factor

    return [
        [round(center["longitude"] - delta_lng, 8), round(center["latitude"] - delta_lat, 8)],
        [round(center["longitude"] + delta_lng, 8), round(center["latitude"] - delta_lat, 8)],
        [round(center["longitude"] + delta_lng, 8), round(center["latitude"] + delta_lat, 8)],
        [round(center["longitude"] - delta_lng, 8), round(center["latitude"] + delta_lat, 8)],
    ]


def split_area_into_zones(area_feature):
    area_ring = get_polygon_ring(area_feature)
    area_points = normalize_points(area_ring)
    area_center = calculate_center(area_points)
    total_area_sqm = polygon_area_sqm(area_ring)
    chunk_area_sqm = get_chunk_area_sqm()
    zone_count = max(1, math.ceil(total_area_sqm / chunk_area_sqm))

    zones = []
    remaining_area = total_area_sqm
    base_longitude = area_center["longitude"]
    base_latitude = area_center["latitude"]

    for sequence in range(zone_count):
        zone_area_sqm = min(chunk_area_sqm, remaining_area) if sequence < zone_count - 1 else remaining_area
        if zone_area_sqm <= 0:
            zone_area_sqm = min(chunk_area_sqm, total_area_sqm)

        shift = (sequence - ((zone_count - 1) / 2)) * 0.0003
        zone_center = {
            "longitude": round(base_longitude + shift, 8),
            "latitude": round(base_latitude, 8),
        }
        zone_points = build_zone_square(area_points, zone_center, zone_area_sqm)
        zone_geometry = {
            "type": "Polygon",
            "coordinates": [[*zone_points, zone_points[0]]],
        }
        zones.append(
            {
                "zone_id": f"zone-{sequence}",
                "geometry": zone_geometry,
                "points": zone_points,
                "center": zone_center,
                "area_sqm": zone_area_sqm,
                "area_hectares": zone_area_sqm / 10000,
                "sequence": sequence,
            }
        )
        remaining_area = max(0.0, remaining_area - zone_area_sqm)

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
            "zone_count": zone_count,
        },
        "zones": zones,
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
        zone.processing_status = CropZone.STATUS_COMPLETED
        zone.processing_error = ""
        zone.save(update_fields=["processing_status", "processing_error", "updated_at"])
    except Exception as exc:
        zone.processing_status = CropZone.STATUS_FAILED
        zone.processing_error = str(exc)
        zone.save(update_fields=["processing_status", "processing_error", "updated_at"])
        raise

    return zone


def dispatch_zone_processing_tasks(crop_area_id):
    from .tasks import process_zone_soil_data

    zones = list(CropZone.objects.filter(crop_area_id=crop_area_id).only("id"))
    for zone in zones:
        task_identifier = ""
        try:
            async_result = process_zone_soil_data.delay(zone.id)
            task_identifier = getattr(async_result, "id", "") or ""
        except Exception:
            analyze_and_store_zone_soil_data(zone_id=zone.id)
        CropZone.objects.filter(id=zone.id).update(task_id=task_identifier)


def create_zones_and_dispatch(area_feature):
    ensure_products_exist()
    area_feature = normalize_area_feature(area_feature)
    zoning_result = split_area_into_zones(area_feature)
    area_data = zoning_result["area"]

    with transaction.atomic():
        crop_area = CropArea.objects.create(
            geometry=area_data["geometry"],
            points=area_data["points"],
            center=area_data["center"],
            area_sqm=round(area_data["area_sqm"], 2),
            area_hectares=round(area_data["area_hectares"], 4),
            chunk_area_sqm=round(area_data["chunk_area_sqm"], 2),
            zone_count=area_data["zone_count"],
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

    crop_area.refresh_from_db()
    dispatch_zone_processing_tasks(crop_area.id)
    return crop_area, zones


def _zones_queryset(zone_ids=None):
    queryset = CropZone.objects.select_related(
        "recommendation__product",
        "water_need_layer",
        "soil_quality_layer",
        "cultivation_risk_layer",
    ).prefetch_related(
        Prefetch("recommendation__criteria", queryset=CropZoneCriteria.objects.order_by("sequence", "id"))
    ).order_by("sequence", "id")
    if zone_ids:
        queryset = queryset.filter(zone_id__in=zone_ids)
    return queryset


def get_latest_area_payload():
    area = CropArea.objects.order_by("-created_at", "-id").first()
    if area:
        return {"area": area.geometry}
    return {"area": get_default_area_feature()}


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


def get_zone_details_payload(zone_id):
    zone = _zones_queryset().get(zone_id=zone_id)
    recommendation = getattr(zone, "recommendation", None)
    criteria = recommendation.criteria.all() if recommendation else []
    return {
        "zoneId": zone.zone_id,
        "crop": recommendation.product.product_id if recommendation else "",
        "matchPercent": recommendation.match_percent if recommendation else 0,
        "waterNeed": recommendation.water_need if recommendation else "",
        "estimatedProfit": recommendation.estimated_profit if recommendation else "",
        "reason": recommendation.reason if recommendation else "",
        "criteria": [{"name": item.name, "value": item.value} for item in criteria],
        "area_hectares": zone.area_hectares,
    }
