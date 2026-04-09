from urllib.parse import urljoin

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import QueryDict
from farm_hub.models import FarmHub

from .catalog import GOLD_PLAN_CODE
from .models import AccessFeature, AccessRule, FarmAccessProfile, SubscriptionPlan


class AccessControlError(Exception):
    pass


class AccessControlServiceUnavailable(AccessControlError):
    pass


ACTION_MAP = {
    "GET": "view",
    "HEAD": "view",
    "OPTIONS": "view",
    "POST": "create",
    "PUT": "edit",
    "PATCH": "edit",
    "DELETE": "delete",
}


def get_default_subscription_plan():
    return SubscriptionPlan.objects.filter(is_active=True, metadata__is_default=True).order_by("name").first()


def get_effective_subscription_plan(farm):
    if farm.subscription_plan_id:
        return farm.subscription_plan

    default_plan = get_default_subscription_plan()
    if default_plan is not None:
        return default_plan

    return SubscriptionPlan.objects.filter(code=GOLD_PLAN_CODE, is_active=True).order_by("name").first()


def _match_rule(rule, farm, subscription_plan, product_ids, sensor_catalog_ids, sensor_catalog_codes):
    if not rule.is_active:
        return False

    if rule.subscription_plans.exists() and (subscription_plan is None or not rule.subscription_plans.filter(pk=subscription_plan.pk).exists()):
        return False

    if rule.farm_types.exists() and not rule.farm_types.filter(pk=farm.farm_type_id).exists():
        return False

    if rule.products.exists() and not rule.products.filter(pk__in=product_ids).exists():
        return False

    if rule.sensor_catalogs.exists() and not rule.sensor_catalogs.filter(pk__in=sensor_catalog_ids).exists():
        return False

    metadata_sensor_codes = rule.metadata.get("sensor_catalog_codes", [])
    if metadata_sensor_codes and not set(metadata_sensor_codes).intersection(sensor_catalog_codes):
        return False

    return True


def build_farm_access_profile(farm):
    farm = FarmHub.objects.select_related("farm_type", "subscription_plan").prefetch_related(
        "products",
        "sensors",
        "sensors__sensor_catalog",
    ).get(pk=farm.pk)

    subscription_plan = get_effective_subscription_plan(farm)
    product_ids = list(farm.products.values_list("id", flat=True))
    sensor_catalog_ids = list(
        farm.sensors.exclude(sensor_catalog__isnull=True).values_list("sensor_catalog_id", flat=True)
    )
    sensor_catalog_codes = set(
        farm.sensors.exclude(sensor_catalog__isnull=True).values_list("sensor_catalog__code", flat=True)
    )

    features = {
        feature.code: {
            "name": feature.name,
            "type": feature.feature_type,
            "enabled": feature.default_enabled,
            "source": "default" if feature.default_enabled else None,
        }
        for feature in AccessFeature.objects.filter(is_active=True)
    }

    matched_rules = []
    rules = AccessRule.objects.filter(is_active=True).prefetch_related(
        "features",
        "subscription_plans",
        "farm_types",
        "products",
        "sensor_catalogs",
    ).order_by("priority", "id")

    for rule in rules:
        if not _match_rule(rule, farm, subscription_plan, product_ids, sensor_catalog_ids, sensor_catalog_codes):
            continue

        matched_rules.append(
            {
                "code": rule.code,
                "name": rule.name,
                "effect": rule.effect,
                "priority": rule.priority,
            }
        )
        for feature in rule.features.all():
            feature_state = features.setdefault(
                feature.code,
                {
                    "name": feature.name,
                    "type": feature.feature_type,
                    "enabled": feature.default_enabled,
                    "source": "default" if feature.default_enabled else None,
                },
            )
            feature_state["enabled"] = rule.effect == AccessRule.ALLOW
            feature_state["source"] = rule.code

    profile = {
        "farm_uuid": str(farm.farm_uuid),
        "subscription_plan": None,
        "features": features,
        "matched_rules": matched_rules,
        "resolved_from_profile": True,
    }
    if subscription_plan is not None:
        profile["subscription_plan"] = {
            "uuid": str(subscription_plan.uuid),
            "code": subscription_plan.code,
            "name": subscription_plan.name,
        }

    FarmAccessProfile.objects.update_or_create(
        farm=farm,
        defaults={
            "subscription_plan": subscription_plan,
            "profile_data": profile,
            "resolved_from_profile": True,
        },
    )
    return profile


def build_opa_resource(farm):
    subscription_plan = get_effective_subscription_plan(farm)
    sensor_codes = list(
        farm.sensors.exclude(sensor_catalog__isnull=True).values_list("sensor_catalog__code", flat=True)
    )
    power_sensor = []
    for sensor in farm.sensors.all():
        if isinstance(sensor.power_source, dict):
            power_type = sensor.power_source.get("type")
            if power_type:
                power_sensor.append(power_type)

    return {
        "farm_id": str(farm.farm_uuid),
        "subscription_plan_codes": [subscription_plan.code] if subscription_plan else [],
        "farm_types": [farm.farm_type.name] if farm.farm_type_id else [],
        "crop_types": list(farm.products.values_list("name", flat=True)),
        "cultivation_types": [],
        "sensor_codes": sensor_codes,
        "power_sensor": power_sensor,
        "customization": [],
    }


def build_opa_user(user):
    return {
        "id": getattr(user, "id", None),
        "username": getattr(user, "username", ""),
        "email": getattr(user, "email", ""),
        "phone_number": getattr(user, "phone_number", ""),
        "is_staff": bool(getattr(user, "is_staff", False)),
        "is_superuser": bool(getattr(user, "is_superuser", False)),
        "role": "farmer",
    }


def get_authorization_action(method):
    return ACTION_MAP.get(method.upper(), "view")


def _opa_url(path):
    base_url = getattr(settings, "ACCESS_CONTROL_AUTHZ_BASE_URL", "").strip()
    if not base_url:
        raise ImproperlyConfigured("ACCESS_CONTROL_AUTHZ_BASE_URL is not configured.")
    return urljoin(f"{base_url.rstrip('/')}/", path.lstrip("/"))


def build_authorization_input(farm, user, features, action):
    return {
        "user": build_opa_user(user),
        "resource": build_opa_resource(farm),
        "features": list(features),
        "action": action,
    }


def request_opa_batch_authorization(farm, user, features, action):
    if not getattr(settings, "ACCESS_CONTROL_AUTHZ_ENABLED", True):
        return {"decisions": {feature: True for feature in features}}

    if not features:
        return {"decisions": {}}

    payload = {"input": build_authorization_input(farm, user, features, action)}

    try:
        response = requests.post(
            _opa_url(settings.ACCESS_CONTROL_AUTHZ_BATCH_PATH),
            json=payload,
            timeout=settings.ACCESS_CONTROL_AUTHZ_TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise AccessControlServiceUnavailable("OPA authorization service is unavailable.") from exc

    try:
        return response.json().get("result", {})
    except ValueError as exc:
        raise AccessControlServiceUnavailable("OPA authorization service returned invalid JSON.") from exc


def normalize_opa_batch_result(data, features):
    decisions = data.get("decisions")
    if isinstance(decisions, dict):
        return {feature: bool(decisions.get(feature, False)) for feature in features}

    allowed_features = data.get("allowed_features")
    if isinstance(allowed_features, list):
        allowed = set(allowed_features)
        return {feature: feature in allowed for feature in features}

    if isinstance(data, dict) and all(isinstance(value, bool) for value in data.values()):
        return {feature: bool(data.get(feature, False)) for feature in features}

    raise AccessControlServiceUnavailable("OPA authorization service returned an unsupported payload.")


def batch_authorize_features(farm, user, features, action):
    result = request_opa_batch_authorization(farm, user, features, action)
    return normalize_opa_batch_result(result, features)


def authorize_feature(farm, user, feature_code, action):
    return batch_authorize_features(farm, user, [feature_code], action).get(feature_code, False)


def get_request_data(request):
    if isinstance(request.data, QueryDict):
        return request.data
    if isinstance(request.data, dict):
        return request.data
    return {}
