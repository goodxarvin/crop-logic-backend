"""
Static mock data for Irrigation Recommendation API.
No database, no dynamic values.
"""

CONFIG_RESPONSE_DATA = {
    "farmInfo": {
        "soilType": "Loamy",
        "waterQuality": "Medium EC",
        "climateZone": "Temperate",
    },
    "cropOptions": [
        {"id": "wheat", "labelKey": "wheat", "icon": "tabler-wheat"},
        {"id": "corn", "labelKey": "corn", "icon": "tabler-plant-2"},
        {"id": "cotton", "labelKey": "cotton", "icon": "tabler-flower"},
        {"id": "saffron", "labelKey": "saffron", "icon": "tabler-flower-2"},
        {"id": "canola", "labelKey": "canola", "icon": "tabler-leaf"},
        {"id": "vegetables", "labelKey": "vegetables", "icon": "tabler-carrot"},
    ],
}

RECOMMEND_RESPONSE_DATA = {
    "plan": {
        "frequencyPerWeek": 4,
        "durationMinutes": 45,
        "bestTimeOfDay": "05:00 - 07:00",
        "moistureLevel": 72,
        "warning": "Avoid irrigation during midday hours in the coming week due to forecasted high temperatures.",
    },
}
