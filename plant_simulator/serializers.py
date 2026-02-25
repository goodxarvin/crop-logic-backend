"""
Response serialization for Plant Simulator API.
Plain Django; no DRF. Builds response envelope only. All payloads are static mock data.

Request: on POST /start the client must send a body with keys matching the sliders
from config (light, water, soil_ph) plus growth_speed. See START_REQUEST_EXAMPLE.
No validation or use of request in response; backend returns static mock only.
"""

from .mock_data import CONFIG_SLIDERS_ONLY

# ---------------------------------------------------------------------------
# POST /start — بدنه‌ای که کلاینت باید ارسال کند (مطابق اسلایدرهای config)
# ---------------------------------------------------------------------------

# کلیدهای environment (همان key هر اسلایدر به‌جز growth_speed)
START_ENVIRONMENT_KEYS = [
    item["key"]
    for item in CONFIG_SLIDERS_ONLY["sliders"]
    if item["key"] != "growth_speed"
]

# مقدار پیش‌فرض هر اسلایدر برای ساخت نمونه درخواست
def _defaults_from_sliders():
    return {
        item["key"]: item["default_value"]
        for item in CONFIG_SLIDERS_ONLY["sliders"]
    }

# نمونه بدنه درخواست start که کلاینت باید ارسال کند
START_REQUEST_EXAMPLE = {
    "environment": {
        k: v for k, v in _defaults_from_sliders().items() if k != "growth_speed"
    },
    "growth_speed": _defaults_from_sliders().get("growth_speed", 1.5),
}

# برای سازگاری: همان ساختار به صورت ثابت (بدون وابستگی به محاسبه)
START_REQUEST_EXAMPLE_STATIC = {
    "environment": {
        "light": 75,
        "water": 65,
        "soil_ph": 6.5,
    },
    "growth_speed": 1.5,
}


def success_response():
    """
    Response when endpoint does not return data.
    Returns: {"status": "success"}
    """
    return {"status": "success"}


def success_with_data(data):
    """
    Response when endpoint returns data.
    Returns: {"status": "success", "data": data}
    """
    return {"status": "success", "data": data}
