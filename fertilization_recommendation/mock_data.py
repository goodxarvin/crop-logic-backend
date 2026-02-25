"""
Static mock data for Fertilization Recommendation API.
No database, no dynamic values.
"""

CONFIG_RESPONSE_DATA = {
    "farmData": {
        "soilType": "Loamy",
        "organicMatter": "Medium (2.5%)",
        "waterEC": "1.2 dS/m",
    },
    "growthStages": [
        {"id": "prePlanting", "icon": "tabler-seedling"},
        {"id": "earlyGrowth", "icon": "tabler-leaf"},
        {"id": "flowering", "icon": "tabler-flower"},
        {"id": "fruiting", "icon": "tabler-apple"},
        {"id": "postHarvest", "icon": "tabler-basket"},
    ],
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
        "npkRatio": "20-20-20 (NPK)",
        "amountPerHectare": "150 kg/ha",
        "applicationMethod": "Foliar spray + soil broadcast",
        "applicationInterval": "Every 14 days",
        "reasoning": "Your loamy soil with medium organic matter (2.5%) provides good nutrient retention. Water EC of 1.2 dS/m indicates low salinity—suitable for most crops. At the flowering stage, increased phosphorus supports bloom development. We recommend a balanced NPK to maintain nitrogen for vegetative growth while boosting phosphorous for flowering.",
    },
}
