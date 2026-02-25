"""
Static mock data for Plant Simulator API.
Matches PLANT_SIMULATOR_API.md. No database, no dynamic values.
Smooth animation: 51 points (0–10s, ~5 frames per second).
"""

# ---------------------------------------------------------------------------
# GET /api/plant-simulator/config  (ورود: فقط اسلایدرها)
# ---------------------------------------------------------------------------

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
            "unit": "×",
            "default_value": 1.5,
        },
    ],
}

# ---------------------------------------------------------------------------
# POST /api/plant-simulator/start  (ثابت‌ها + چارت کانفیگ + plant + progress + chart)
# ---------------------------------------------------------------------------

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

# 51 نقطه برای انیمیشن نرم (۰ تا ۱۰ ثانیه، هر ~۰٫۲s)
_labels = [f"{i * 0.2:.1f}s" for i in range(51)]
_height = [round(142 * (i / 50) ** 0.9) for i in range(51)]  # رشد کمی شتاب‌دار
_leaf = [min(5, int(i / 10)) for i in range(51)]  # 0,0..,1,1..,2,...,5
_yield = [round(12.4 * (i / 50) ** 1.2, 1) for i in range(51)]  # محصول با شتاب ملایم
_yield_rate = [round(0.087 * max(0, (i - 15) / 35), 3) for i in range(51)]  # نرخ از ثانیه ~۳

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

# ---------------------------------------------------------------------------
# GET /api/plant-simulator/state  (plant + progress + chart history)
# ---------------------------------------------------------------------------

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