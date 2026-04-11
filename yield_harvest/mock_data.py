"""
Static mock data for Yield & Harvest Prediction API.
Mirrors the yieldPredictionChart and harvestPredictionCard dashboard card shapes.
"""

CONFIG_SLIDERS_ONLY = {
    "sliders": [
        {
            "key": "light",
            "label": "نور",
            "min": 0,
            "max": 100,
            "step": 5,
            "unit_type": "percent",
            "default_value": 75,
            "icon": "☀️",
        },
        {
            "key": "water",
            "label": "آب",
            "min": 0,
            "max": 100,
            "step": 5,
            "unit_type": "percent",
            "default_value": 65,
            "icon": "💧",
        },
        {
            "key": "soil_ph",
            "label": "pH خاک",
            "min": 4,
            "max": 9,
            "step": 0.5,
            "unit_type": "number",
            "unit": "",
            "default_value": 6.5,
        },
        {
            "key": "growth_speed",
            "label": "سرعت رشد",
            "min": 0.5,
            "max": 5,
            "step": 0.5,
            "unit_type": "number",
            "unit": "x",
            "default_value": 1.5,
        },
    ],
}

CONSTANTS = {
    "max_height": 280,
    "max_leaves": 14,
    "max_branches": 6,
    "max_yield": 500,
    "yield_unit": "g",
    "yield_rate_unit": "g/s",
    "height_unit": "px",
}

CHART_CONFIG = {
    "title": "پیشرفت رشد",
    "x_axis_label": "زمان (ثانیه)",
    "series": [
        {
            "key": "height",
            "label": "ارتفاع (px)",
            "y_axis_id": "yHeight",
            "min": 0,
            "max": 280,
            "unit": "px",
        },
        {
            "key": "leaves",
            "label": "تعداد برگ",
            "y_axis_id": "yLeaf",
            "min": 0,
            "max": 14,
        },
        {
            "key": "yield",
            "label": "محصول (g)",
            "y_axis_id": "yYield",
            "min": 0,
            "max": 500,
            "unit": "g",
        },
        {
            "key": "yield_rate",
            "label": "نرخ محصول (g/s)",
            "y_axis_id": "yYieldRate",
            "min": 0,
            "unit": "g/s",
        },
    ],
}

_labels = [f"{i * 0.2:.1f}s" for i in range(51)]
_height = [round(142 * (i / 50) ** 0.9) for i in range(51)]
_leaf = [min(5, int(i / 10)) for i in range(51)]
_yield = [round(12.4 * (i / 50) ** 1.2, 1) for i in range(51)]
_yield_rate = [round(0.087 * max(0, (i - 15) / 35), 3) for i in range(51)]

START_RESPONSE_DATA = {
    "constants": CONSTANTS,
    "chart": CHART_CONFIG,
    "plant": {
        "height": 142,
        "leaves_count": 5,
        "branches_count": 2,
        "fruits_count": 0,
        "yield": 12.4,
        "yield_rate": 0.087,
        "tick": 520,
        "is_healthy": True,
        "can_continue": True,
    },
    "progress": {
        "growth_progress": 50,
        "light_status": 75,
        "water_status": 65,
        "yield_progress": 2.5,
        "yield_current": 12.4,
        "yield_rate_current": 0.087,
    },
    "chart_history": {
        "labels": _labels,
        "height_history": _height,
        "leaf_history": _leaf,
        "yield_history": _yield,
        "yield_rate_history": _yield_rate,
    },
}

STATE_RESPONSE_DATA = {
    "plant": {
        "height": 142,
        "leaves_count": 5,
        "branches_count": 2,
        "fruits_count": 0,
        "yield": 12.4,
        "yield_rate": 0.087,
        "tick": 520,
        "is_healthy": True,
        "can_continue": True,
    },
    "progress": {
        "growth_progress": 50,
        "light_status": 75,
        "water_status": 65,
        "yield_progress": 2.5,
        "yield_current": 12.4,
        "yield_rate_current": 0.087,
    },
    "chart": {
        "labels": _labels,
        "height_history": _height,
        "leaf_history": _leaf,
        "yield_history": _yield,
        "yield_rate_history": _yield_rate,
    },
}

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
