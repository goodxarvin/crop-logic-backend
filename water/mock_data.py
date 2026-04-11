"""
Static mock data for WATER API.
"""

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

WATER_NEED_PREDICTION = {
    "totalNext7Days": 3290,
    "unit": "m3",
    "categories": ["روز 1", "روز 2", "روز 3", "روز 4", "روز 5", "روز 6", "روز 7"],
    "series": [{"name": "نیاز آبی", "data": [420, 450, 480, 460, 490, 510, 480]}],
}

WATER_STRESS_INDEX = {
    "id": "water_stress_index",
    "title": "شاخص تنش آبی",
    "subtitle": "فعلی",
    "stats": "12%",
    "avatarColor": "info",
    "avatarIcon": "tabler-droplet",
    "chipText": "پایین",
    "chipColor": "success",
}
