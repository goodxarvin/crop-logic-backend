"""
Static mock data for Farm Dashboard API.
No database, no dynamic values. Pure static payloads.
"""

# Config payload for GET/PATCH farm-dashboard-config (section 2.1)
# row_order must use valid row IDs only: overviewKpis, weatherAlerts, sensorMonitoring,
# sensorCharts, alertsWater, predictions, soilHeatmap, ndviRecommendations, economic
CONFIG = {
    "disabled_card_ids": [
        "predictions",
    ],
    "row_order": [
        "overviewKpis",
        "weatherAlerts",
        "sensorMonitoring",
        "sensorCharts",
        "alertsWater",
        "soilHeatmap",
        "ndviRecommendations",
        "economic",
    ],
    "enable_drag_reorder": False,
}

# 4.1 farmOverviewKpis
FARM_OVERVIEW_KPIS = {
    "kpis": [
        {
            "id": "farm_health_score",
            "title": "امتیاز سلامت مزرعه",
            "subtitle": "تحلیل هوشمند",
            "stats": "87%",
            "avatarColor": "success",
            "avatarIcon": "tabler-heartbeat",
            "chipText": "خوب",
            "chipColor": "success",
        },
        {
            "id": "water_stress_index",
            "title": "شاخص تنش آبی",
            "subtitle": "فعلی",
            "stats": "12%",
            "avatarColor": "info",
            "avatarIcon": "tabler-droplet",
            "chipText": "پایین",
            "chipColor": "success",
        },
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
            "id": "avg_soil_moisture",
            "title": "میانگین رطوبت خاک",
            "subtitle": "کل مزرعه",
            "stats": "65%",
            "avatarColor": "primary",
            "avatarIcon": "tabler-plant-2",
            "chipText": "بهینه",
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

# 4.5 sensorRadarChart
SENSOR_RADAR_CHART = {
    "labels": ["دما", "رطوبت", "pH", "هدایت الکتریکی", "نور", "باد"],
    "series": [
        {"name": "امروز", "data": [75, 65, 80, 70, 85, 60]},
        {"name": "ایده‌آل", "data": [80, 70, 75, 75, 90, 50]},
    ],
}

# 4.6 sensorComparisonChart
SENSOR_COMPARISON_CHART = {
    "currentValue": 48,
    "vsLastWeek": "+5%",
    "vsLastWeekValue": 5,
    "categories": ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه", "شنبه", "یکشنبه"],
    "series": [
        {"name": "امروز", "data": [42, 45, 48, 52, 50, 48, 46]},
        {"name": "هفته قبل", "data": [38, 40, 42, 45, 43, 40, 38]},
    ],
}

# 4.7 anomalyDetectionCard
ANOMALY_DETECTION_CARD = {
    "anomalies": [
        {
            "sensor": "رطوبت خاک زون ۳",
            "value": "38%",
            "expected": "45-65%",
            "deviation": "-12%",
            "severity": "warning",
        },
        {
            "sensor": "pH بخش ۲",
            "value": "5.2",
            "expected": "6.0-7.0",
            "deviation": "-0.8",
            "severity": "error",
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

# 4.12 soilMoistureHeatmap
SOIL_MOISTURE_HEATMAP = {
    "zones": ["زون ۱", "زون ۲", "زون ۳", "زون ۴", "زون ۵", "زون ۶", "زون ۷"],
    "hours": ["۶ ص", "۸ ص", "۱۰ ص", "۱۲ ظ", "۱۴ ع", "۱۶ ع", "۱۸ ع"],
    "series": [
        {
            "name": "زون ۱",
            "data": [
                {"x": "۶ ص", "y": 52},
                {"x": "۸ ص", "y": 48},
                {"x": "۱۰ ص", "y": 55},
                {"x": "۱۲ ظ", "y": 60},
                {"x": "۱۴ ع", "y": 58},
                {"x": "۱۶ ع", "y": 54},
                {"x": "۱۸ ع", "y": 50},
            ],
        },
        {
            "name": "زون ۲",
            "data": [
                {"x": "۶ ص", "y": 45},
                {"x": "۸ ص", "y": 42},
                {"x": "۱۰ ص", "y": 48},
                {"x": "۱۲ ظ", "y": 52},
                {"x": "۱۴ ع", "y": 50},
                {"x": "۱۶ ع", "y": 47},
                {"x": "۱۸ ع", "y": 44},
            ],
        },
    ],
}

# 4.13 ndviHealthCard
NDVI_HEALTH_CARD = {
    "ndviIndex": 0.78,
    "healthData": [
        {"title": "تنش نیتروژن", "value": "پایین", "color": "success", "icon": "tabler-leaf"},
        {"title": "سلامت محصول", "value": "خوب", "color": "success", "icon": "tabler-plant"},
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
    "farmOverviewKpis": FARM_OVERVIEW_KPIS,
    "farmWeatherCard": FARM_WEATHER_CARD,
    "farmAlertsTracker": FARM_ALERTS_TRACKER,
    "sensorValuesList": SENSOR_VALUES_LIST,
    "sensorRadarChart": SENSOR_RADAR_CHART,
    "sensorComparisonChart": SENSOR_COMPARISON_CHART,
    "anomalyDetectionCard": ANOMALY_DETECTION_CARD,
    "farmAlertsTimeline": FARM_ALERTS_TIMELINE,
    "waterNeedPrediction": WATER_NEED_PREDICTION,
    "harvestPredictionCard": HARVEST_PREDICTION_CARD,
    "yieldPredictionChart": YIELD_PREDICTION_CHART,
    "soilMoistureHeatmap": SOIL_MOISTURE_HEATMAP,
    "ndviHealthCard": NDVI_HEALTH_CARD,
    "recommendationsList": RECOMMENDATIONS_LIST,
    "economicOverview": ECONOMIC_OVERVIEW,
}
