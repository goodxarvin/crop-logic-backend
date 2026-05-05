from copy import deepcopy

from .defaults import FERTILIZATION_DASHBOARD_TEMPLATE
from .models import FertilizationPlan, FertilizationRecommendationRequest


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


def get_active_plan_payload(farm):
    if farm is None:
        return {}

    plan = (
        FertilizationPlan.objects.filter(farm=farm, is_active=True, is_deleted=False)
        .order_by("-created_at", "-id")
        .first()
    )
    if plan is None or not isinstance(plan.plan_payload, dict):
        return {}

    return deepcopy(plan.plan_payload)


def build_active_plan_context(farm):
    plan_payload = get_active_plan_payload(farm)
    if not plan_payload:
        return {}

    context = {"plan_payload": plan_payload}

    primary_recommendation = plan_payload.get("primary_recommendation")
    if isinstance(primary_recommendation, dict) and primary_recommendation:
        context["primary_recommendation"] = deepcopy(primary_recommendation)

    nutrient_analysis = plan_payload.get("nutrient_analysis")
    if isinstance(nutrient_analysis, dict) and nutrient_analysis:
        context["nutrient_analysis"] = deepcopy(nutrient_analysis)

    application_guide = plan_payload.get("application_guide")
    if isinstance(application_guide, dict) and application_guide:
        context["application_guide"] = deepcopy(application_guide)

    alternative_recommendations = plan_payload.get("alternative_recommendations")
    if isinstance(alternative_recommendations, list) and alternative_recommendations:
        context["alternative_recommendations"] = deepcopy(alternative_recommendations)

    sections = plan_payload.get("sections")
    if isinstance(sections, list) and sections:
        context["sections"] = deepcopy(sections)

    return context


def get_fertilization_dashboard_recommendation(farm=None):
    default_item = deepcopy(FERTILIZATION_DASHBOARD_TEMPLATE)
    result = _get_latest_result(farm)
    plan = result.get("plan") or {}
    if not isinstance(plan, dict) or not plan:
        return default_item

    npk_ratio = plan.get("npkRatio") or "20-20-20 (NPK)"
    amount = plan.get("amountPerHectare")
    method = plan.get("applicationMethod")
    interval = plan.get("applicationInterval")

    subtitle_parts = [part for part in [amount, method, interval] if part]

    default_item["title"] = f"کود: {npk_ratio}"
    if subtitle_parts:
        default_item["subtitle"] = "، ".join(subtitle_parts)
    default_item["status"] = "success"
    default_item["source"] = "db"
    default_item["warnings"] = []

    return default_item
