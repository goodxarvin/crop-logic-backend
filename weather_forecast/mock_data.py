"""
Static mock data for Weather Forecast API.
Mirrors the farmWeatherCard dashboard card shape.
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
