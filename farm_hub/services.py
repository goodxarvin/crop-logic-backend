import logging

from django.conf import settings
from django.db import transaction

from crop_zoning.services import (
    create_zones_and_dispatch,
    get_default_area_feature,
    get_initial_zones_payload,
    normalize_area_feature,
)
from external_api_adapter import request as external_api_request
from external_api_adapter.exceptions import ExternalAPIRequestError


logger = logging.getLogger(__name__)


class FarmDataSyncError(Exception):
    pass


def dispatch_farm_zoning(area_feature, farm):
    crop_area, _zones = create_zones_and_dispatch(normalize_area_feature(area_feature), farm=farm)
    return crop_area, get_initial_zones_payload(crop_area)


def normalize_farm_boundary_input(area_feature):
    if area_feature is None:
        return get_default_area_feature()

    if not isinstance(area_feature, dict):
        raise ValueError("`farm_boundary` must be a GeoJSON object or corners payload.")

    corners = area_feature.get("corners")
    if isinstance(corners, list) and corners:
        ring = []
        for corner in corners:
            if not isinstance(corner, dict):
                raise ValueError("Each farm boundary corner must be an object.")
            lat = corner.get("lat")
            lon = corner.get("lon")
            if lat is None or lon is None:
                raise ValueError("Each farm boundary corner must include `lat` and `lon`.")
            ring.append([float(lon), float(lat)])

        if ring[0] != ring[-1]:
            ring.append(ring[0])

        area_feature = {
            "type": "Feature",
            "properties": {},
            "geometry": {"type": "Polygon", "coordinates": [ring]},
        }

    return normalize_area_feature(area_feature)


def sync_farm_data(
    *,
    farm,
    area_feature=None,
    sensor_key="sensor-7-1",
    sensor_payload=None,
    plant_ids=None,
    irrigation_method_id=None,
):
    request_payload = {
        "farm_uuid": str(farm.farm_uuid),
        "farm_boundary": _extract_boundary_geometry(area_feature, farm=farm),
    }

    normalized_sensor_payload = _normalize_sensor_payload(sensor_key=sensor_key, sensor_payload=sensor_payload)
    if normalized_sensor_payload:
        request_payload["sensor_key"] = sensor_key or "sensor-7-1"
        request_payload["sensor_payload"] = normalized_sensor_payload

    if plant_ids:
        request_payload["plant_ids"] = [int(plant_id) for plant_id in plant_ids]

    resolved_irrigation_method_id = irrigation_method_id
    if resolved_irrigation_method_id is None:
        resolved_irrigation_method_id = farm.irrigation_method_id
    if resolved_irrigation_method_id is not None:
        request_payload["irrigation_method_id"] = int(resolved_irrigation_method_id)

    if not any(key in request_payload for key in ("sensor_payload", "plant_ids", "irrigation_method_id")):
        raise FarmDataSyncError(
            "At least one of `sensor_payload`, `plant_ids`, or `irrigation_method_id` is required for farm data sync."
        )

    api_key = getattr(settings, "FARM_DATA_API_KEY", "")
    if not api_key:
        logger.error("Farm data sync failed: FARM_DATA_API_KEY missing for farm_uuid=%s", farm.farm_uuid)
        raise FarmDataSyncError("FARM_DATA_API_KEY is not configured.")

    logger.warning(
        "Farm data sync start: farm_uuid=%s sensor_key=%s has_sensor_payload=%s plant_ids=%s irrigation_method_id=%s boundary_type=%s",
        farm.farm_uuid,
        request_payload.get("sensor_key"),
        "sensor_payload" in request_payload,
        request_payload.get("plant_ids"),
        request_payload.get("irrigation_method_id"),
        request_payload["farm_boundary"].get("type") if isinstance(request_payload["farm_boundary"], dict) else None,
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
        logger.exception("Farm data sync request exception: farm_uuid=%s", farm.farm_uuid)
        raise FarmDataSyncError(f"Farm data API request failed: {exc}") from exc

    if response.status_code >= 400:
        response_body = response.data
        logger.error(
            "Farm data sync rejected: farm_uuid=%s status_code=%s response=%s",
            farm.farm_uuid,
            response.status_code,
            response_body,
        )
        raise FarmDataSyncError(f"Farm data API returned status {response.status_code}: {response_body}")

    logger.warning("Farm data sync success: farm_uuid=%s status_code=%s", farm.farm_uuid, response.status_code)
    return request_payload


def create_farm_with_zoning(serializer, owner):
    area_feature = serializer.validated_data.pop("area_geojson", None) or get_default_area_feature()
    sensor_key = serializer.validated_data.pop("sensor_key", "sensor-7-1")
    sensor_payload = serializer.validated_data.pop("sensor_payload", None)
    irrigation_method_id = serializer.validated_data.get("irrigation_method_id", None)

    with transaction.atomic():
        farm = serializer.save(owner=owner)
        crop_area, zoning_payload = dispatch_farm_zoning(area_feature, farm)
        farm.current_crop_area = crop_area
        farm.save(update_fields=["current_crop_area", "updated_at"])
        sync_farm_data(
            farm=farm,
            area_feature=area_feature,
            sensor_key=sensor_key,
            sensor_payload=sensor_payload,
            plant_ids=[product.id for product in farm.products.all()],
            irrigation_method_id=irrigation_method_id,
        )

    return farm, zoning_payload


def _normalize_sensor_payload(*, sensor_key, sensor_payload):
    if not sensor_payload:
        return None
    if not isinstance(sensor_payload, dict):
        raise ValueError("`sensor_payload` must be an object.")

    normalized_sensor_key = sensor_key or "sensor-7-1"
    if all(isinstance(value, dict) for value in sensor_payload.values()):
        return sensor_payload
    return {normalized_sensor_key: sensor_payload}


def _extract_boundary_geometry(area_feature, *, farm):
    if area_feature is not None:
        geometry = (area_feature.get("geometry") or {}) if area_feature.get("type") == "Feature" else area_feature
        if geometry.get("type") != "Polygon":
            raise FarmDataSyncError("Farm boundary geometry must be a Polygon.")
        return geometry

    crop_area = farm.current_crop_area or farm.crop_areas.order_by("-created_at", "-id").first()
    if crop_area is None:
        raise FarmDataSyncError("Farm boundary is not configured for this farm.")

    geometry = crop_area.geometry or {}
    if geometry.get("type") == "Feature":
        geometry = geometry.get("geometry") or {}
    if geometry.get("type") != "Polygon":
        raise FarmDataSyncError("Farm boundary geometry must be a Polygon.")
    return geometry


def _get_farm_data_path():
    return getattr(settings, "FARM_DATA_API_PATH", "/api/farm-data/")
