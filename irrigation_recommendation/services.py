from copy import deepcopy

from .mock_data import IRRIGATION_DASHBOARD_RECOMMENDATION, RECOMMEND_RESPONSE_DATA, WATER_NEED_PREDICTION
from .models import IrrigationRecommendationRequest


def _extract_result(response_payload):
    if not isinstance(response_payload, dict):
        return {}

    data = response_payload.get("data")
    if isinstance(data, dict) and isinstance(data.get("result"), dict):
        return data["result"]

    result = response_payload.get("result")
    if isinstance(result, dict):
        return result

    return {}


def _get_latest_result(farm):
    if farm is None:
        return {}

    for request in IrrigationRecommendationRequest.objects.filter(farm=farm):
        result = _extract_result(request.response_payload)
        if result:
            return result

    return {}


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
