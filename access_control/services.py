import hashlib
import json
from functools import lru_cache
from pathlib import Path
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.core.cache import cache
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


def _get_authz_cache_timeout():
    return int(getattr(settings, "ACCESS_CONTROL_AUTHZ_CACHE_TIMEOUT", 300))


@lru_cache(maxsize=1)
def load_route_feature_map():
    feature_map_path = Path(settings.BASE_DIR) / "config" / "feature.json"
    with feature_map_path.open("r", encoding="utf-8") as feature_map_file:
        return json.load(feature_map_file)


def get_route_feature_code(app_label):
    if not app_label:
        return None
    return load_route_feature_map().get(app_label)


def _get_authorization_cache_key(farm, user, features, action, route):
    raw_key = json.dumps(
        {
            "farm_uuid": str(getattr(farm, "farm_uuid", "")),
            "user_id": getattr(user, "id", None),
            "features": sorted(features),
            "action": action,
            "route": route or "",
        },
        sort_keys=True,
    )
    digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    return f"access-control:authz:{digest}"


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
    if farm is None:
        return {
            "farm_id": None,
            "subscription_plan_codes": [],
            "farm_types": [],
            "crop_types": [],
            "cultivation_types": [],
            "sensor_codes": [],
            "power_sensor": [],
            "customization": [],
        }

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


def build_authorization_input(farm, user, features, action, route=None):
    return {
        "user": build_opa_user(user),
        "resource": build_opa_resource(farm),
        "features": list(features),
        "action": action,
        "route": route,
    }


def request_opa_batch_authorization(farm, user, features, action, route=None):
    if not getattr(settings, "ACCESS_CONTROL_AUTHZ_ENABLED", True):
        return {"decisions": {feature: True for feature in features}}

    if not features:
        return {"decisions": {}}

    payload = {"input": build_authorization_input(farm, user, features, action, route=route)}

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

    feature_results = data.get("features")
    if isinstance(feature_results, dict):
        normalized = {}
        for feature in features:
            feature_result = feature_results.get(feature, {})
            if isinstance(feature_result, dict):
                normalized[feature] = bool(feature_result.get("allow", False))
            else:
                normalized[feature] = bool(feature_result)
        return normalized

    allowed_features = data.get("allowed_features")
    if isinstance(allowed_features, list):
        allowed = set(allowed_features)
        return {feature: feature in allowed for feature in features}

    if isinstance(data, dict) and all(isinstance(value, bool) for value in data.values()):
        return {feature: bool(data.get(feature, False)) for feature in features}

    raise AccessControlServiceUnavailable("OPA authorization service returned an unsupported payload.")


def batch_authorize_features(farm, user, features, action, route=None):
    if not features:
        return {}

    cache_key = _get_authorization_cache_key(farm, user, features, action, route)

    try:
        cached_result = cache.get(cache_key)
    except Exception:
        cached_result = None

    if isinstance(cached_result, dict):
        return {feature: bool(cached_result.get(feature, False)) for feature in features}

    result = request_opa_batch_authorization(farm, user, features, action, route=route)
    decisions = normalize_opa_batch_result(result, features)

    try:
        cache.set(cache_key, decisions, timeout=_get_authz_cache_timeout())
    except Exception:
        pass

    return decisions


def authorize_feature(farm, user, feature_code, action, route=None):
    return batch_authorize_features(farm, user, [feature_code], action, route=route).get(feature_code, False)


def get_request_data(request):
    request_data = getattr(request, "data", None)
    if isinstance(request_data, QueryDict):
        return request_data
    if isinstance(request_data, dict):
        return request_data

    cached_body = getattr(request, "_access_control_request_data", None)
    if isinstance(cached_body, dict):
        return cached_body

    content_type = (getattr(request, "content_type", "") or "").split(";")[0].strip().lower()
    body = getattr(request, "body", b"") or b""
    if not body:
        return {}

    if content_type == "application/json":
        try:
            parsed_body = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return {}
        if isinstance(parsed_body, dict):
            request._access_control_request_data = parsed_body
            return parsed_body
        return {}

    return {}
