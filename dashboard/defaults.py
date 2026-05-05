from copy import deepcopy


VALID_ROW_IDS = [
    "overviewKpis",
    "weatherAlerts",
    "sensorMonitoring",
    "sensorCharts",
    "alertsWater",
    "predictions",
    "soilHeatmap",
    "ndviRecommendations",
    "economic",
]

VALID_CARD_IDS = [
    "farmOverviewKpis",
    "farmWeatherCard",
    "farmAlertsTracker",
    "sensorValuesList",
    "sensorRadarChart",
    "sensorComparisonChart",
    "anomalyDetectionCard",
    "farmAlertsTimeline",
    "waterNeedPrediction",
    "harvestPredictionCard",
    "yieldPredictionChart",
    "soilMoistureHeatmap",
    "ndviHealthCard",
    "recommendationsList",
    "economicOverview",
]

DEFAULT_CONFIG = {
    "disabled_card_ids": [],
    "row_order": VALID_ROW_IDS.copy(),
    "enable_drag_reorder": True,
}


def get_default_dashboard_config():
    return deepcopy(DEFAULT_CONFIG)
