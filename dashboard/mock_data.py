"""
Backward-compatible mock exports for dashboard fake content.

Use `dashboard.defaults` for runtime configuration defaults and
`dashboard.templates` for fallback card payload templates.
"""

from .defaults import DEFAULT_CONFIG, VALID_CARD_IDS, VALID_ROW_IDS
from .templates import (
    ALL_CARD_TEMPLATES as ALL_CARDS,
    ECONOMIC_OVERVIEW,
    FARM_ALERTS_TIMELINE,
    FARM_ALERTS_TRACKER,
    FARM_OVERVIEW_KPIS,
    FARM_WEATHER_CARD,
    HARVEST_PREDICTION_CARD,
    RECOMMENDATIONS_LIST,
    SENSOR_VALUES_LIST,
    WATER_NEED_PREDICTION,
    YIELD_PREDICTION_CHART,
)
