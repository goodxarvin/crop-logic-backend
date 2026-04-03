from django.utils import timezone

from .catalog import GOLD_PLAN_CODE
from .models import AccessFeature, AccessRule, FarmAccessProfile, SubscriptionPlan


def _manager_id_set(manager):
    return {obj.id for obj in manager.all()}


def get_effective_subscription_plan(farm):
    if getattr(farm, "subscription_plan_id", None):
        return farm.subscription_plan

    return (
        SubscriptionPlan.objects.filter(is_active=True, metadata__is_default=True).order_by("name").first()
        or SubscriptionPlan.objects.filter(code=GOLD_PLAN_CODE, is_active=True).first()
    )


def rule_matches_farm(rule, farm, product_ids=None, sensor_catalog_ids=None):
    if not rule.is_active:
        return False

    subscription_plan_ids = _manager_id_set(rule.subscription_plans)
    if subscription_plan_ids:
        subscription_plan = get_effective_subscription_plan(farm)
        if subscription_plan is None or subscription_plan.id not in subscription_plan_ids:
            return False

    farm_type_ids = _manager_id_set(rule.farm_types)
    if farm_type_ids and farm.farm_type_id not in farm_type_ids:
        return False

    product_rule_ids = _manager_id_set(rule.products)
    if product_rule_ids:
        product_ids = product_ids if product_ids is not None else set(farm.products.values_list("id", flat=True))
        if not product_ids or product_rule_ids.isdisjoint(product_ids):
            return False

    sensor_catalog_rule_ids = _manager_id_set(rule.sensor_catalogs)
    if sensor_catalog_rule_ids:
        sensor_catalog_ids = (
            sensor_catalog_ids
            if sensor_catalog_ids is not None
            else set(farm.sensors.exclude(sensor_catalog_id__isnull=True).values_list("sensor_catalog_id", flat=True))
        )
        if not sensor_catalog_ids or sensor_catalog_rule_ids.isdisjoint(sensor_catalog_ids):
            return False

    sensor_catalog_rule_codes = set(rule.metadata.get("sensor_catalog_codes", [])) if isinstance(rule.metadata, dict) else set()
    if sensor_catalog_rule_codes:
        farm_sensor_catalog_codes = set(
            farm.sensors.exclude(sensor_catalog__code__isnull=True).values_list("sensor_catalog__code", flat=True)
        )
        if not farm_sensor_catalog_codes or sensor_catalog_rule_codes.isdisjoint(farm_sensor_catalog_codes):
            return False

    sensor_catalog_rule_names = set(rule.metadata.get("sensor_catalog_names", [])) if isinstance(rule.metadata, dict) else set()
    if sensor_catalog_rule_names:
        farm_sensor_catalog_names = set(
            farm.sensors.exclude(sensor_catalog__name__isnull=True).values_list("sensor_catalog__name", flat=True)
        )
        if not farm_sensor_catalog_names or sensor_catalog_rule_names.isdisjoint(farm_sensor_catalog_names):
            return False

    return True


def build_farm_access_profile(farm):
    subscription_plan = get_effective_subscription_plan(farm)
    features = AccessFeature.objects.all().order_by("feature_type", "code")
    resolved = {
        feature.code: {
            "enabled": feature.default_enabled,
            "type": feature.feature_type,
            "name": feature.name,
            "description": feature.description,
            "metadata": feature.metadata,
            "source": "default",
        }
        for feature in features
    }

    product_ids = set(farm.products.values_list("id", flat=True))
    sensor_catalog_ids = set(farm.sensors.exclude(sensor_catalog_id__isnull=True).values_list("sensor_catalog_id", flat=True))

    rules = (
        AccessRule.objects.filter(is_active=True, features__isnull=False)
        .distinct()
        .prefetch_related("features", "subscription_plans", "farm_types", "products", "sensor_catalogs")
        .order_by("priority", "id")
    )

    matched_rules = []
    for rule in rules:
        if not rule_matches_farm(rule, farm, product_ids=product_ids, sensor_catalog_ids=sensor_catalog_ids):
            continue

        matched_rules.append(
            {
                "code": rule.code,
                "name": rule.name,
                "effect": rule.effect,
                "priority": rule.priority,
            }
        )
        is_enabled = rule.effect == AccessRule.ALLOW
        for feature in rule.features.all():
            resolved[feature.code] = {
                "enabled": is_enabled,
                "type": feature.feature_type,
                "name": feature.name,
                "description": feature.description,
                "metadata": feature.metadata,
                "source": rule.code,
            }

    grouped = {}
    for code, payload in resolved.items():
        grouped.setdefault(f"{payload['type']}s", {})[code] = payload

    profile, _created = FarmAccessProfile.objects.update_or_create(
        farm=farm,
        defaults={
            "cached_features": resolved,
            "cached_groups": grouped,
            "matched_rules": matched_rules,
            "last_resolved_at": timezone.now(),
        },
    )

    return {
        "farm_uuid": str(farm.farm_uuid),
        "subscription_plan": {
            "uuid": str(subscription_plan.uuid),
            "code": subscription_plan.code,
            "name": subscription_plan.name,
        }
        if subscription_plan is not None
        else None,
        "features": profile.cached_features,
        "groups": profile.cached_groups,
        "matched_rules": profile.matched_rules,
        "resolved_from_profile": True,
    }


def build_farm_access_profile_response(farm):
    profile_data = build_farm_access_profile(farm)
    return {
        "farm_uuid": profile_data["farm_uuid"],
        "subscription_plan": profile_data["subscription_plan"],
        "matched_rules": profile_data["matched_rules"],
        "resolved_from_profile": profile_data["resolved_from_profile"],
    }


def is_feature_enabled_for_farm(farm, feature_code):
    profile = getattr(farm, "access_profile", None)
    if profile and isinstance(profile.cached_features, dict):
        feature_payload = profile.cached_features.get(feature_code)
        if feature_payload is not None:
            return bool(feature_payload.get("enabled"))

    profile_data = build_farm_access_profile(farm)
    feature_payload = profile_data["features"].get(feature_code)
    if feature_payload is None:
        return False
    return bool(feature_payload.get("enabled"))
