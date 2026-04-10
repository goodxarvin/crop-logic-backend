"""
Static mock data for Yield & Harvest Prediction API.
Mirrors the yieldPredictionChart and harvestPredictionCard dashboard card shapes.
"""

YIELD_PREDICTION_CARD = {
    "id": "yield_prediction",
    "title": "پیش‌بینی عملکرد",
    "subtitle": "این فصل",
    "stats": "42 تن",
    "avatarColor": "secondary",
    "avatarIcon": "tabler-chart-bar",
    "chipText": "+8%",
    "chipColor": "success",
}

YIELD_PREDICTION_CHART = {
    "categories": [
        "ژانویه", "فوریه", "مارس", "آوریل", "می", "ژوئن",
        "ژوئیه", "آگوست", "سپتامبر", "اکتبر", "نوامبر", "دسامبر",
    ],
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

HARVEST_PREDICTION_CARD = {
    "date": "2025-10-15",
    "dateFormatted": "۱۵ اکتبر ۲۰۲۵",
    "daysUntil": 58,
    "description": "بر اساس تجمع GDD فعلی و پیش‌بینی آب و هوا. بازه بهینه برداشت: ۱۲ تا ۱۸ اکتبر.",
    "optimalWindowStart": "2025-10-12",
    "optimalWindowEnd": "2025-10-18",
}
