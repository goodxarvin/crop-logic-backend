from copy import deepcopy

from .mock_data import FERTILIZATION_DASHBOARD_RECOMMENDATION, RECOMMEND_RESPONSE_DATA
from .models import FertilizationRecommendationRequest


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

    for request in FertilizationRecommendationRequest.objects.filter(farm=farm):
        result = _extract_result(request.response_payload)
        if result:
            return result

    return {}


def get_fertilization_dashboard_recommendation(farm=None):
    default_item = deepcopy(FERTILIZATION_DASHBOARD_RECOMMENDATION)
    result = _get_latest_result(farm)
    plan = result.get("plan") or RECOMMEND_RESPONSE_DATA.get("plan", {})

    npk_ratio = plan.get("npkRatio") or "20-20-20 (NPK)"
    amount = plan.get("amountPerHectare")
    method = plan.get("applicationMethod")
    interval = plan.get("applicationInterval")

    subtitle_parts = [part for part in [amount, method, interval] if part]

    default_item["title"] = f"کود: {npk_ratio}"
    if subtitle_parts:
        default_item["subtitle"] = "، ".join(subtitle_parts)

    return default_item
