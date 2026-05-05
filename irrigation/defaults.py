CONFIG_RESPONSE_TEMPLATE = {
    "farmInfo": {
        "soilType": None,
        "waterQuality": None,
        "climateZone": None,
    },
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


IRRIGATION_DASHBOARD_TEMPLATE = {
    "title": "آبیاری",
    "subtitle": "داده توصیه آبیاری هنوز ثبت نشده است.",
    "avatarIcon": "tabler-droplet",
    "avatarColor": "primary",
    "status": "empty",
    "source": "db",
    "warnings": ["No persisted irrigation recommendation is available for this farm."],
}
