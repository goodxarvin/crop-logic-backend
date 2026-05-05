from copy import deepcopy

from water.services import (
    get_farm_weather_card_data,
    get_water_need_prediction_data,
    get_water_stress_index_data,
)
from crop_health.services import get_crop_health_summary_data
from economic_overview.services import get_economic_overview_data
from farm_alerts.services import (
    get_alert_timeline_data,
    get_alert_tracker_data,
    get_recommendations_list_data,
)
from fertilization.services import get_fertilization_dashboard_recommendation
from irrigation.services import get_irrigation_dashboard_recommendation
from pest_detection.services import get_risk_summary_data
from device_hub.services import (
    get_sensor_7_in_1_summary_data,
)
from yield_harvest.services import get_yield_harvest_summary_data

from .templates import get_all_card_templates


def _update_kpi(card_lookup, card_data):
    if not card_data:
        return

    card_id = card_data.get("id")
    if not card_id or card_id not in card_lookup:
        return

    details = card_data.get("details")
    clean_data = {key: value for key, value in card_data.items() if key != "details"}
    card_lookup[card_id].update(clean_data)
    if details is not None:
        card_lookup[card_id]["details"] = details


def _build_overview_kpis(base_cards, crop_health_summary, water_stress_index, avg_soil_moisture, risk_summary, yield_summary):
    kpis = [crop_health_summary["farmHealthScore"], water_stress_index, avg_soil_moisture, *deepcopy(base_cards["kpis"])]
    card_lookup = {item["id"]: item for item in kpis}

    _update_kpi(card_lookup, water_stress_index)
    _update_kpi(card_lookup, avg_soil_moisture)
    _update_kpi(card_lookup, risk_summary.get("disease_risk", {}))
    _update_kpi(card_lookup, risk_summary.get("pest_risk", {}))
    _update_kpi(card_lookup, yield_summary.get("yield_prediction_card", {}))

    return {"kpis": kpis}


def _build_recommendations_list(farm, fallback_data, harvest_card):
    recommendations = []
    recommendations.extend(get_recommendations_list_data(farm).get("recommendations", []))
    recommendations.append(get_irrigation_dashboard_recommendation(farm))
    recommendations.append(get_fertilization_dashboard_recommendation(farm))

    if harvest_card:
        recommendations.append(
            {
                "title": f"بازه برداشت: {harvest_card.get('optimalWindowStart', '')} تا {harvest_card.get('optimalWindowEnd', '')}",
                "subtitle": harvest_card.get("description", ""),
                "avatarIcon": "tabler-calendar-event",
                "avatarColor": "info",
            }
        )

    deduped = []
    seen_titles = set()
    for item in recommendations:
        title = item.get("title")
        if not title or title in seen_titles:
            continue
        seen_titles.add(title)
        deduped.append(item)

    if deduped:
        return {"recommendations": deduped[:4]}

    return deepcopy(fallback_data)


def get_farm_dashboard_cards(farm):
    cards = get_all_card_templates()

    water_cards = {
        "farmWeatherCard": get_farm_weather_card_data(farm),
        "waterNeedPrediction": get_water_need_prediction_data(farm),
        "waterStressIndex": get_water_stress_index_data(farm),
    }
    crop_health_summary = get_crop_health_summary_data(farm)
    risk_summary = get_risk_summary_data(farm)
    yield_summary = get_yield_harvest_summary_data(farm)
    sensor_summary = get_sensor_7_in_1_summary_data(farm)
    alert_cards = {
        "farmAlertsTracker": get_alert_tracker_data(farm),
        "farmAlertsTimeline": get_alert_timeline_data(farm),
    }
    economic_overview = get_economic_overview_data(farm)
    avg_soil_moisture = sensor_summary["avgSoilMoisture"]

    cards["farmWeatherCard"] = water_cards["farmWeatherCard"]
    cards["farmAlertsTracker"] = alert_cards["farmAlertsTracker"]
    cards["farmAlertsTimeline"] = alert_cards["farmAlertsTimeline"]
    cards["sensorValuesList"] = sensor_summary["sensorValuesList"]
    cards["anomalyDetectionCard"] = sensor_summary["anomalyDetectionCard"]
    cards["waterNeedPrediction"] = water_cards["waterNeedPrediction"]
    cards["harvestPredictionCard"] = yield_summary["harvest_prediction_card"]
    cards["yieldPredictionChart"] = yield_summary["yield_prediction_chart"]
    cards["sensorRadarChart"] = sensor_summary["sensorRadarChart"]
    cards["sensorComparisonChart"] = sensor_summary["sensorComparisonChart"]
    cards["soilMoistureHeatmap"] = sensor_summary["soilMoistureHeatmap"]
    cards["ndviHealthCard"] = crop_health_summary["ndviHealthCard"]
    cards["economicOverview"] = economic_overview
    cards["farmOverviewKpis"] = _build_overview_kpis(
        cards["farmOverviewKpis"],
        crop_health_summary,
        water_cards["waterStressIndex"],
        avg_soil_moisture,
        risk_summary,
        yield_summary,
    )
    cards["recommendationsList"] = _build_recommendations_list(
        farm,
        cards["recommendationsList"],
        yield_summary.get("harvest_prediction_card", {}),
    )

    return cards
