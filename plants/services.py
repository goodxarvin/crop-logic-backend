from django.db import transaction
from django.conf import settings

from external_api_adapter import request as external_api_request
from external_api_adapter.exceptions import ExternalAPIRequestError
from farm_hub.models import FarmType, Product


DEFAULT_FARM_TYPE_NAME = "زراعی"
DEFAULT_ICON = "leaf"
DEFAULT_GROWTH_STAGES = [
    "initial",
    "vegetative",
    "flowering",
    "fruiting",
    "maturity",
]
AI_FARM_DATA_PLANT_SYNC_PATH = "/api/farm-data/plants/sync/"


class PlantSyncError(Exception):
    pass


def _clean_stage_name(value):
    stage = str(value or "").strip()
    return stage


def _merge_growth_stages(product, supplied_stages=None):
    stages = []
    seen = set()
    has_explicit_stage_data = False

    for stage in supplied_stages or []:
        normalized = _clean_stage_name(stage)
        if normalized and normalized not in seen:
            has_explicit_stage_data = True
            seen.add(normalized)
            stages.append(normalized)

    current_stage = _clean_stage_name(getattr(product, "growth_stage", ""))
    if current_stage and current_stage not in seen:
        has_explicit_stage_data = True
        seen.add(current_stage)
        stages.append(current_stage)

    if not has_explicit_stage_data:
        for stage in DEFAULT_GROWTH_STAGES:
            seen.add(stage)
            stages.append(stage)

    thresholds = product.growth_profile.get("stage_thresholds", {}) if isinstance(product.growth_profile, dict) else {}
    if isinstance(thresholds, dict):
        for stage_name in thresholds.keys():
            normalized = _clean_stage_name(stage_name)
            if normalized and normalized not in seen:
                seen.add(normalized)
                stages.append(normalized)

    return stages


@transaction.atomic
def ensure_plant_defaults(queryset=None):
    products = list(queryset if queryset is not None else Product.objects.all())
    updated_products = []

    for product in products:
        changed = False

        if not product.icon:
            product.icon = DEFAULT_ICON
            changed = True

        normalized_stages = _merge_growth_stages(product, product.growth_stages)
        if normalized_stages != (product.growth_stages or []):
            product.growth_stages = normalized_stages
            changed = True

        if not product.growth_stage and product.growth_stages:
            product.growth_stage = product.growth_stages[0]
            changed = True

        if changed:
            updated_products.append(product)

    if updated_products:
        Product.objects.bulk_update(updated_products, ["icon", "growth_stage", "growth_stages"])

    return products


def serialize_products_for_ai(products=None):
    products = list(products if products is not None else Product.objects.select_related("farm_type").all().order_by("name"))
    ensure_plant_defaults(products)
    payload = []
    for product in products:
        payload.append(
            {
                "id": product.id,
                "name": product.name,
                "slug": "",
                "icon": product.icon,
                "description": product.description,
                "metadata": product.metadata if isinstance(product.metadata, dict) else {},
                "light": product.light,
                "watering": product.watering,
                "soil": product.soil,
                "temperature": product.temperature,
                "growth_stage": product.growth_stage,
                "growth_stages": product.growth_stages or [],
                "planting_season": product.planting_season,
                "harvest_time": product.harvest_time,
                "spacing": product.spacing,
                "fertilizer": product.fertilizer,
                "health_profile": product.health_profile if isinstance(product.health_profile, dict) else {},
                "irrigation_profile": product.irrigation_profile if isinstance(product.irrigation_profile, dict) else {},
                "growth_profile": product.growth_profile if isinstance(product.growth_profile, dict) else {},
                "is_active": True,
                "updated_at": product.updated_at.isoformat() if product.updated_at else None,
                "farm_type": product.farm_type.name if product.farm_type_id else DEFAULT_FARM_TYPE_NAME,
            }
        )
    return payload


def push_plants_to_ai(products=None):
    api_key = getattr(settings, "FARM_DATA_API_KEY", "")
    if not api_key:
        raise PlantSyncError("FARM_DATA_API_KEY is not configured.")

    payload = serialize_products_for_ai(products)
    try:
        adapter_response = external_api_request(
            "ai",
            AI_FARM_DATA_PLANT_SYNC_PATH,
            method="POST",
            payload=payload,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-API-Key": api_key,
                "Authorization": f"Api-Key {api_key}",
            },
        )
    except ExternalAPIRequestError as exc:
        raise PlantSyncError(str(exc)) from exc

    if adapter_response.status_code >= 400:
        raise PlantSyncError(f"AI service returned status {adapter_response.status_code}.")
    return payload
