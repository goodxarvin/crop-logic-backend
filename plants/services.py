from django.db import transaction

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
AI_PLANTS_PATH = "/api/plants/"


class PlantSyncError(Exception):
    pass


def _extract_plant_items(adapter_data):
    if isinstance(adapter_data, list):
        return adapter_data
    if not isinstance(adapter_data, dict):
        return []

    data = adapter_data.get("data")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        result = data.get("result")
        if isinstance(result, list):
            return result

    result = adapter_data.get("result")
    if isinstance(result, list):
        return result
    return []


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


@transaction.atomic
def sync_plants_from_ai():
    try:
        adapter_response = external_api_request("ai", AI_PLANTS_PATH, method="GET")
    except ExternalAPIRequestError as exc:
        raise PlantSyncError(str(exc)) from exc

    if adapter_response.status_code >= 400:
        raise PlantSyncError(f"AI service returned status {adapter_response.status_code}.")

    products = []
    for item in _extract_plant_items(adapter_response.data):
        if not isinstance(item, dict):
            continue

        name = str(item.get("name") or "").strip()
        if not name:
            continue

        farm_type_name = str(item.get("farm_type") or DEFAULT_FARM_TYPE_NAME).strip() or DEFAULT_FARM_TYPE_NAME
        farm_type, _ = FarmType.objects.get_or_create(name=farm_type_name)

        growth_profile = item.get("growth_profile") if isinstance(item.get("growth_profile"), dict) else {}
        growth_stages = item.get("growth_stages") if isinstance(item.get("growth_stages"), list) else []
        normalized_growth_stages = []
        for stage in growth_stages:
            normalized = _clean_stage_name(stage)
            if normalized:
                normalized_growth_stages.append(normalized)

        defaults = {
            "description": str(item.get("description") or "").strip(),
            "metadata": item.get("metadata") if isinstance(item.get("metadata"), dict) else {},
            "light": str(item.get("light") or "").strip(),
            "watering": str(item.get("watering") or "").strip(),
            "soil": str(item.get("soil") or "").strip(),
            "temperature": str(item.get("temperature") or "").strip(),
            "growth_stage": str(item.get("growth_stage") or "").strip(),
            "growth_stages": normalized_growth_stages,
            "planting_season": str(item.get("planting_season") or "").strip(),
            "harvest_time": str(item.get("harvest_time") or "").strip(),
            "spacing": str(item.get("spacing") or "").strip(),
            "fertilizer": str(item.get("fertilizer") or "").strip(),
            "icon": str(item.get("icon") or "").strip(),
            "health_profile": item.get("health_profile") if isinstance(item.get("health_profile"), dict) else {},
            "irrigation_profile": item.get("irrigation_profile") if isinstance(item.get("irrigation_profile"), dict) else {},
            "growth_profile": growth_profile,
        }
        product, _ = Product.objects.update_or_create(
            farm_type=farm_type,
            name=name,
            defaults=defaults,
        )
        products.append(product)

    ensure_plant_defaults(products)
    return products
