from django.db import transaction

from crop_zoning.services import create_zones_and_dispatch, get_initial_zones_payload, normalize_area_feature


def create_sensor_with_zoning(serializer, owner):
    area_feature = serializer.validated_data.pop("area_geojson", None)

    with transaction.atomic():
        sensor = serializer.save(owner=owner)
        zoning_payload = None

        if area_feature is not None:
            crop_area, _zones = create_zones_and_dispatch(normalize_area_feature(area_feature))
            zoning_payload = get_initial_zones_payload(crop_area)

    return sensor, zoning_payload
