CONFIG_RESPONSE_TEMPLATE = {
    "farmData": {
        "soilType": None,
        "organicMatter": None,
        "waterEC": None,
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
    "status": "success",
    "source": "default_template",
}


FERTILIZATION_DASHBOARD_TEMPLATE = {
    "title": "کود",
    "subtitle": "داده توصیه کودهی هنوز ثبت نشده است.",
    "avatarIcon": "tabler-leaf",
    "avatarColor": "success",
    "status": "empty",
    "source": "db",
    "warnings": ["No persisted fertilization recommendation is available for this farm."],
}
