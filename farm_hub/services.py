from django.db import transaction

from crop_zoning.services import (
    create_zones_and_dispatch,
    get_default_area_feature,
    get_initial_zones_payload,
    normalize_area_feature,
)


def dispatch_farm_zoning(area_feature, farm):
    crop_area, _zones = create_zones_and_dispatch(normalize_area_feature(area_feature), farm=farm)
    return crop_area, get_initial_zones_payload(crop_area)


def create_farm_with_zoning(serializer, owner):
    area_feature = serializer.validated_data.pop("area_geojson", None) or get_default_area_feature()

    with transaction.atomic():
        farm = serializer.save(owner=owner)
        crop_area, zoning_payload = dispatch_farm_zoning(area_feature, farm)
        farm.current_crop_area = crop_area
        farm.save(update_fields=["current_crop_area", "updated_at"])

    return farm, zoning_payload
