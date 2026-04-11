"""
Static mock data for Farm Dashboard API.
"""

from copy import deepcopy
from threading import Lock


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

_config_lock = Lock()
_config_state = deepcopy(DEFAULT_CONFIG)


def get_config():
    with _config_lock:
        return deepcopy(_config_state)


def update_config(changes):
    with _config_lock:
        _config_state.update(deepcopy(changes))
        return deepcopy(_config_state)


def reset_config():
    with _config_lock:
        _config_state.clear()
        _config_state.update(deepcopy(DEFAULT_CONFIG))
        return deepcopy(_config_state)

# 4.1 farmOverviewKpis
FARM_OVERVIEW_KPIS = {
    "kpis": [
        {
            "id": "disease_risk",
            "title": "ریسک بیماری",
            "subtitle": "۷ روز اخیر",
            "stats": "پایین",
            "avatarColor": "success",
            "avatarIcon": "tabler-bug",
            "chipText": "5%",
            "chipColor": "success",
        },
        {
            "id": "yield_prediction",
            "title": "پیش‌بینی عملکرد",
            "subtitle": "این فصل",
            "stats": "42 تن",
            "avatarColor": "secondary",
            "avatarIcon": "tabler-chart-bar",
            "chipText": "+8%",
            "chipColor": "success",
        },
        {
            "id": "pest_risk",
            "title": "ریسک آفات",
            "subtitle": "پیش‌بینی هوشمند",
            "stats": "15%",
            "avatarColor": "warning",
            "avatarIcon": "tabler-bug-off",
            "chipText": "تحت نظر",
            "chipColor": "warning",
        },
    ]
}

# 4.2 farmWeatherCard
FARM_WEATHER_CARD = {
    "condition": "صاف",
    "temperature": 24,
    "unit": "°C",
    "humidity": 45,
    "windSpeed": 12,
    "windUnit": "km/h",
    "chartData": {
        "labels": ["۶ صبح", "۹ صبح", "۱۲ ظهر", "۳ بعدازظهر", "۶ عصر", "۹ شب", "۱۲ شب"],
        "series": [[18, 22, 26, 28, 25, 20, 18]],
    },
}

# 4.3 farmAlertsTracker
FARM_ALERTS_TRACKER = {
    "totalAlerts": 3,
    "radialBarValue": 30,
    "alertStats": [
        {
            "title": "کمبود آب",
            "count": "2",
            "avatarColor": "error",
            "avatarIcon": "tabler-droplet-half-2",
        },
        {
            "title": "ریسک قارچی",
            "count": "1",
            "avatarColor": "warning",
            "avatarIcon": "tabler-mushroom",
        },
        {
            "title": "هشدار یخبندان",
            "count": "0",
            "avatarColor": "info",
            "avatarIcon": "tabler-snowflake",
        },
    ],
}

# 4.4 sensorValuesList
SENSOR_VALUES_LIST = {
    "sensors": [
        {
            "title": "28°C",
            "subtitle": "دمای هوا",
            "trendNumber": 2.1,
            "trend": "positive",
            "unit": "°C",
        },
        {
            "title": "24°C",
            "subtitle": "دمای خاک",
            "trendNumber": -0.5,
            "trend": "negative",
            "unit": "°C",
        },
        {
            "title": "65%",
            "subtitle": "رطوبت هوا",
            "trendNumber": 3.2,
            "trend": "positive",
            "unit": "%",
        },
        {
            "title": "42%",
            "subtitle": "رطوبت خاک (۱۰ سانتی‌متر)",
            "trendNumber": -1.8,
            "trend": "negative",
            "unit": "%",
        },
        {
            "title": "6.8",
            "subtitle": "pH خاک",
            "trendNumber": 0.2,
            "trend": "positive",
            "unit": "pH",
        },
        {
            "title": "1.2",
            "subtitle": "هدایت الکتریکی (dS/m)",
            "trendNumber": 0.1,
            "trend": "positive",
            "unit": "dS/m",
        },
        {
            "title": "850",
            "subtitle": "شدت نور (لوکس)",
            "trendNumber": 15.3,
            "trend": "positive",
            "unit": "lux",
        },
        {
            "title": "12",
            "subtitle": "سرعت باد (کیلومتر/ساعت)",
            "trendNumber": -2.4,
            "trend": "negative",
            "unit": "km/h",
        },
    ]
}

# 4.8 farmAlertsTimeline
FARM_ALERTS_TIMELINE = {
    "alerts": [
        {
            "title": "ریسک کمبود آب",
            "description": "رطوبت خاک در عمق ۱۰ سانتی‌متر (۴۲٪) کمتر از حد بهینه است. پیش‌بینی: در صورت عدم آبیاری، تنش طی ۲ تا ۳ روز. توصیه: آبیاری ظرف ۲۴ ساعت.",
            "time": "۱۵ دقیقه پیش",
            "color": "warning",
        },
        {
            "title": "ریسک بیماری قارچی",
            "description": "رطوبت بالا (۶۵٪) و دمای ۲۴ درجه شرایط مساعد برای رشد قارچ. استفاده از قارچ‌کش پیشگیرانه یا کاهش آبیاری را در نظر بگیرید.",
            "time": "۱ ساعت پیش",
            "color": "error",
        },
        {
            "title": "پیشنهاد آبیاری",
            "description": "بازه بهینه آبیاری: ۶:۰۰ تا ۸:۰۰ صبح. حجم پیشنهادی: ۴۵۰ مترمکعب برای زون آ. بهبود راندمان مورد انتظار: ۱۲٪.",
            "time": "۲ ساعت پیش",
            "color": "info",
        },
        {
            "title": "بررسی شوری خاک",
            "description": "مقدار هدایت الکتریکی ۱/۲ dS/m در محدوده مجاز است. نیازی به اقدام نیست. بررسی بعدی توصیه می‌شود ظرف ۵ روز.",
            "time": "۴ ساعت پیش",
            "color": "success",
        },
    ]
}

# 4.9 waterNeedPrediction
WATER_NEED_PREDICTION = {
    "totalNext7Days": 3290,
    "unit": "m³",
    "categories": ["روز ۱", "روز ۲", "روز ۳", "روز ۴", "روز ۵", "روز ۶", "روز ۷"],
    "series": [{"name": "نیاز آبی", "data": [420, 450, 480, 460, 490, 510, 480]}],
}

# 4.10 harvestPredictionCard
HARVEST_PREDICTION_CARD = {
    "date": "2025-10-15",
    "dateFormatted": "۱۵ اکتبر ۲۰۲۵",
    "daysUntil": 58,
    "description": "بر اساس تجمع GDD فعلی و پیش‌بینی آب و هوا. بازه بهینه برداشت: ۱۲ تا ۱۸ اکتبر.",
    "optimalWindowStart": "2025-10-12",
    "optimalWindowEnd": "2025-10-18",
}

# 4.11 yieldPredictionChart
YIELD_PREDICTION_CHART = {
    "categories": ["ژانویه", "فوریه", "مارس", "آوریل", "می", "ژوئن", "ژوئیه", "آگوست", "سپتامبر", "اکتبر", "نوامبر", "دسامبر"],
    "series": [
        {"name": "امسال", "data": [35, 38, 40, 42, 45, 48, 50, 48, 46, 44, 42, 42]},
        {"name": "سال گذشته", "data": [32, 34, 36, 38, 40, 42, 44, 42, 40, 38, 36, 38]},
    ],
    "summary": [
        {
            "title": "عملکرد پیش‌بینی‌شده",
            "subtitle": "این فصل",
            "amount": "42 تن",
            "avatarColor": "primary",
            "avatarIcon": "tabler-chart-bar",
        },
        {
            "title": "تاریخ برداشت",
            "subtitle": "حدود ۱۵ اکتبر",
            "amount": "+8%",
            "avatarColor": "success",
            "avatarIcon": "tabler-calendar",
        },
    ],
}

# 4.14 recommendationsList
RECOMMENDATIONS_LIST = {
    "recommendations": [
        {
            "title": "آبیاری: ۶:۰۰ تا ۸:۰۰ صبح",
            "subtitle": "۴۵۰ مترمکعب برای زون آ. بدون آبیاری، عملکرد ممکن است حدود ۸٪ کاهش یابد.",
            "avatarIcon": "tabler-droplet",
            "avatarColor": "primary",
        },
        {
            "title": "کود: NPK 20-20-20",
            "subtitle": "اعمال ۲۵ کیلوگرم در هکتار ظرف ۷ روز. کمبود نیتروژن فعلی در بخش ۲.",
            "avatarIcon": "tabler-leaf",
            "avatarColor": "success",
        },
        {
            "title": "قارچ‌کش: پیشگیرانه",
            "subtitle": "رطوبت و دما مساعد قارچ. سمپاشی بر پایه مس را در نظر بگیرید.",
            "avatarIcon": "tabler-mushroom",
            "avatarColor": "warning",
        },
        {
            "title": "بازه برداشت: ۱۲ تا ۱۸ اکتبر",
            "subtitle": "اوج رسیدگی حدود ۱۵ اکتبر. نیروی کار را متناسب برنامه‌ریزی کنید.",
            "avatarIcon": "tabler-calendar-event",
            "avatarColor": "info",
        },
    ]
}

# 4.15 economicOverview
ECONOMIC_OVERVIEW = {
    "economicData": [
        {
            "title": "هزینه آب",
            "value": "€720",
            "subtitle": "این ماه",
            "avatarIcon": "tabler-droplet",
            "avatarColor": "primary",
        },
        {
            "title": "صرفه‌جویی آب هوشمند",
            "value": "€156",
            "subtitle": "۱۸٪ صرفه‌جویی شده",
            "avatarIcon": "tabler-bulb",
            "avatarColor": "success",
        },
        {
            "title": "بازده سرمایه پلتفرم",
            "value": "127%",
            "subtitle": "نسبت به سال گذشته",
            "avatarIcon": "tabler-chart-line",
            "avatarColor": "info",
        },
        {
            "title": "پیش‌بینی درآمد",
            "value": "€42k",
            "subtitle": "این فصل",
            "avatarIcon": "tabler-currency-euro",
            "avatarColor": "success",
        },
    ],
    "chartSeries": [
        {"name": "هزینه آب", "data": [120, 115, 110, 125, 118, 122]},
        {"name": "کود", "data": [80, 85, 90, 75, 82, 78]},
    ],
    "chartCategories": ["ژانویه", "فوریه", "مارس", "آوریل", "می", "ژوئن"],
}

# Unified response for GET /api/farm-dashboard (section 5)
ALL_CARDS = {
    "farmOverviewKpis": FARM_OVERVIEW_KPIS , # این باید سه روز یکبار محتواش محاسبه بشه
    "farmWeatherCard": FARM_WEATHER_CARD, # هروز
    "farmAlertsTracker": FARM_ALERTS_TRACKER, #هروز
    "sensorValuesList": SENSOR_VALUES_LIST,#هروز
    "sensorRadarChart": {},
    "sensorComparisonChart": {},
    "anomalyDetectionCard": {},
    "farmAlertsTimeline": FARM_ALERTS_TIMELINE,
    "waterNeedPrediction": WATER_NEED_PREDICTION,
    "harvestPredictionCard": HARVEST_PREDICTION_CARD,
    "yieldPredictionChart": YIELD_PREDICTION_CHART,
    "soilMoistureHeatmap": {},
    "ndviHealthCard": {},
    "recommendationsList": RECOMMENDATIONS_LIST, # این باید حتما از recommendetion ها گرفته بشه 
    "economicOverview": ECONOMIC_OVERVIEW,
}
