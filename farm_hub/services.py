from django.db import transaction

from crop_zoning.services import create_zones_and_dispatch, get_initial_zones_payload, normalize_area_feature


def dispatch_farm_zoning(area_feature, farm):
    crop_area, _zones = create_zones_and_dispatch(normalize_area_feature(area_feature), farm=farm)
    return get_initial_zones_payload(crop_area)


def create_farm_with_zoning(serializer, owner):
    area_feature = serializer.validated_data.pop("area_geojson", None)

    with transaction.atomic():
        farm = serializer.save(owner=owner)
        zoning_payload = None

        if area_feature is not None:
            zoning_payload = dispatch_farm_zoning(area_feature, farm)

    return farm, zoning_payload
