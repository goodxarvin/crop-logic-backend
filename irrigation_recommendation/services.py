from copy import deepcopy

from .mock_data import IRRIGATION_DASHBOARD_RECOMMENDATION, RECOMMEND_RESPONSE_DATA, WATER_NEED_PREDICTION
from .models import IrrigationRecommendationRequest


def _extract_result(response_payload):
    if not isinstance(response_payload, dict):
        return {}

    data = response_payload.get("data")
    if isinstance(data, dict):
        if isinstance(data.get("result"), dict):
            return data["result"]
        if any(key in data for key in ("plan", "water_balance", "timeline", "sections")):
            return data

    result = response_payload.get("result")
    if isinstance(result, dict):
        return result

    if any(key in response_payload for key in ("plan", "water_balance", "timeline", "sections")):
        return response_payload

    return {}


def _get_latest_result(farm):
    if farm is None:
        return {}

    for request in IrrigationRecommendationRequest.objects.filter(farm=farm).order_by("-created_at", "-id"):
        result = _extract_result(request.response_payload)
        if result:
            return result

    return {}


def _normalize_plan(plan):
    if not isinstance(plan, dict):
        return {}

    normalized = {}
    for key in ("frequencyPerWeek", "durationMinutes", "bestTimeOfDay", "moistureLevel", "warning"):
        value = plan.get(key)
        if value is not None:
            normalized[key] = value
    return normalized


def _normalize_crop_profile(crop_profile):
    if not isinstance(crop_profile, dict):
        return {}

    normalized = {}
    for key in ("kc_initial", "kc_mid", "kc_end"):
        value = crop_profile.get(key)
        if value is not None:
            normalized[key] = value
    return normalized


def _normalize_daily_entries(daily_entries):
    if not isinstance(daily_entries, list):
        return []

    normalized_daily = []
    allowed_keys = (
        "forecast_date",
        "et0_mm",
        "etc_mm",
        "effective_rainfall_mm",
        "gross_irrigation_mm",
        "irrigation_timing",
    )
    for entry in daily_entries:
        if not isinstance(entry, dict):
            continue
        normalized_entry = {key: entry.get(key) for key in allowed_keys if entry.get(key) is not None}
        if normalized_entry:
            normalized_daily.append(normalized_entry)

    return normalized_daily


def _normalize_water_balance(water_balance):
    if not isinstance(water_balance, dict):
        return {}

    normalized = {}
    if water_balance.get("active_kc") is not None:
        normalized["active_kc"] = water_balance.get("active_kc")

    crop_profile = _normalize_crop_profile(water_balance.get("crop_profile"))
    if crop_profile:
        normalized["crop_profile"] = crop_profile

    normalized["daily"] = _normalize_daily_entries(water_balance.get("daily"))
    return normalized


def _normalize_timeline(timeline):
    if not isinstance(timeline, list):
        return []

    normalized_timeline = []
    for item in timeline:
        if not isinstance(item, dict):
            continue
        normalized_item = {}
        for key in ("step_number", "title", "description"):
            value = item.get(key)
            if value is not None:
                normalized_item[key] = value
        if normalized_item:
            normalized_timeline.append(normalized_item)

    return normalized_timeline


def _normalize_sections(raw_sections):
    if not isinstance(raw_sections, list):
        return []

    allowed_keys = {
        "type",
        "title",
        "icon",
        "content",
        "items",
        "frequency",
        "amount",
        "timing",
        "validityPeriod",
        "expandableExplanation",
    }

    normalized_sections = []
    for section in raw_sections:
        if not isinstance(section, dict) or not section.get("type"):
            continue

        normalized_section = {}
        for key in allowed_keys:
            value = section.get(key)
            if value is None:
                continue
            if key == "items":
                if not isinstance(value, list):
                    continue
                normalized_section[key] = [str(item) for item in value]
                continue
            normalized_section[key] = str(value) if key != "type" else value

        normalized_sections.append(normalized_section)
    return normalized_sections


def build_recommendation_response(adapter_payload):
    result = _extract_result(adapter_payload)
    fallback_plan = RECOMMEND_RESPONSE_DATA.get("plan", {})

    return {
        "plan": _normalize_plan(result.get("plan") or fallback_plan),
        "water_balance": _normalize_water_balance(result.get("water_balance")),
        "timeline": _normalize_timeline(result.get("timeline")),
        "sections": _normalize_sections(result.get("sections")),
    }


def get_water_need_prediction_data(farm=None):
    default_data = deepcopy(WATER_NEED_PREDICTION)
    result = _get_latest_result(farm)
    water_balance = result.get("water_balance", {})
    daily = water_balance.get("daily", [])

    if not daily:
        return default_data

    categories = [item.get("forecast_date") or f"روز {index + 1}" for index, item in enumerate(daily)]
    series_data = [float(item.get("gross_irrigation_mm") or 0) for item in daily]

    return {
        "totalNext7Days": round(sum(series_data), 2),
        "unit": "mm",
        "categories": categories,
        "series": [{"name": "نیاز آبی", "data": series_data}],
    }


def get_irrigation_dashboard_recommendation(farm=None):
    default_item = deepcopy(IRRIGATION_DASHBOARD_RECOMMENDATION)
    result = _get_latest_result(farm)
    plan = result.get("plan") or RECOMMEND_RESPONSE_DATA.get("plan", {})

    best_time = plan.get("bestTimeOfDay") or "05:00 - 07:00"
    frequency = plan.get("frequencyPerWeek")
    duration = plan.get("durationMinutes")
    moisture = plan.get("moistureLevel")
    warning = plan.get("warning")

    subtitle_parts = []
    if frequency is not None and duration is not None:
        subtitle_parts.append(f"{frequency} نوبت در هفته، {duration} دقیقه برای هر نوبت")
    if moisture is not None:
        subtitle_parts.append(f"رطوبت هدف {moisture}%")
    if warning:
        subtitle_parts.append(str(warning))

    default_item["title"] = f"آبیاری: {best_time}"
    if subtitle_parts:
        default_item["subtitle"] = ". ".join(subtitle_parts)

    return default_item
