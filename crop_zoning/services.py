import math
from copy import deepcopy

from django.conf import settings
from django.db import transaction

from .models import CropArea, CropZone

EARTH_RADIUS_METERS = 6378137.0


def get_chunk_area_sqm():
    raw_value = getattr(settings, "CROP_ZONE_CHUNK_AREA_SQM", 0)
    try:
        chunk_area = float(raw_value)
    except (TypeError, ValueError):
        chunk_area = 0
    if chunk_area <= 0:
        raise ValueError("CROP_ZONE_CHUNK_AREA_SQM must be a positive number.")
    return chunk_area


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
            "type": "Feature",
            "properties": {
                "zone_id": f"zone-{sequence}",
                "sequence": sequence,
                "area_sqm": round(zone_area_sqm, 2),
                "area_hectares": round(zone_area_sqm / 10000, 4),
                "center": zone_center,
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[*zone_points, zone_points[0]]],
            },
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

    area_geometry = deepcopy(area_feature)
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


def persist_zones(area_feature):
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

        CropZone.objects.bulk_create(
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

    zoning_result["area"]["id"] = crop_area.id
    zoning_result["area"]["uuid"] = str(crop_area.uuid)
    return zoning_result
