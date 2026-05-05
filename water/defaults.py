EMPTY_FARM_WEATHER_CARD = {
    "condition": None,
    "temperature": None,
    "unit": "°C",
    "humidity": None,
    "windSpeed": None,
    "windUnit": "km/h",
    "chartData": {"labels": [], "series": [[]]},
    "status": "empty",
    "source": "db",
    "warnings": ["No persisted weather data is available for this farm."],
}

EMPTY_WATER_NEED_PREDICTION = {
    "totalNext7Days": 0,
    "unit": "mm",
    "categories": [],
    "series": [{"name": "نیاز آبی", "data": []}],
    "status": "empty",
    "source": "db",
    "warnings": ["No persisted irrigation water-balance data is available for this farm."],
}

EMPTY_WATER_STRESS_INDEX = {
    "id": "water_stress_index",
    "title": "شاخص تنش آبی",
    "subtitle": "فعلی",
    "stats": None,
    "avatarColor": "secondary",
    "avatarIcon": "tabler-droplet",
    "chipText": "بدون داده",
    "chipColor": "secondary",
    "status": "empty",
    "source": "db",
    "warnings": ["No persisted irrigation stress data is available for this farm."],
}
