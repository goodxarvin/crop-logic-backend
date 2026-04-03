GOLD_PLAN_CODE = "gold"
SENSOR_7_NAME = "Sensor 7 - Soil Moisture Sensor v1.2"


DEFAULT_SUBSCRIPTION_PLANS = [
    {
        "code": "gold",
        "name": "Gold",
        "description": "Default premium subscription plan with full CropLogic access.",
        "metadata": {"is_default": True},
    },
]


DEFAULT_ACCESS_FEATURES = [
    {"code": "dashboards", "name": "داشبوردها", "feature_type": "section"},
    {"code": "data-section", "name": "بخش داده ها", "feature_type": "section"},
    {"code": "water-data", "name": "دیتاهای آب", "feature_type": "page"},
    {"code": "soil-information", "name": "اطلاعات خاک", "feature_type": "page"},
    {"code": "crop-zoning", "name": "زون بندی کشت", "feature_type": "page"},
    {"code": "simulator", "name": "شبیه ساز", "feature_type": "section"},
    {"code": "plant-growth-simulator", "name": "شبیه ساز رشد گیاه", "feature_type": "page"},
    {"code": "recommendations", "name": "توصیه ها", "feature_type": "section"},
    {"code": "irrigation-recommendation", "name": "توصیه آبیاری", "feature_type": "page"},
    {"code": "fertilization-recommendation", "name": "توصیه کوددهی", "feature_type": "page"},
    {"code": "smart-assistant", "name": "دستیار هوشمند", "feature_type": "section"},
    {"code": "farm-ai-assistant", "name": "دستیار هوشمند مزرعه", "feature_type": "page"},
    {"code": "pest-detection", "name": "تشخیص آفات گیاهی", "feature_type": "page"},
    {"code": "sensor-page", "name": "صفحه سنسور", "feature_type": "page"},
    {"code": "greenhouse-dashboard", "name": "Greenhouse Dashboard", "feature_type": "page"},
]


DEFAULT_ACCESS_RULES = [
    {
        "code": "gold-full-access",
        "name": "Gold Full Access",
        "description": "Enables all core product features for gold subscribers.",
        "effect": "allow",
        "priority": 10,
        "subscription_plans": ["gold"],
        "features": [
            "dashboards",
            "data-section",
            "water-data",
            "soil-information",
            "crop-zoning",
            "simulator",
            "plant-growth-simulator",
            "recommendations",
            "irrigation-recommendation",
            "fertilization-recommendation",
            "smart-assistant",
            "farm-ai-assistant",
            "pest-detection",
            "greenhouse-dashboard",
        ],
    },
    {
        "code": "sensor-7-page-access",
        "name": "Sensor 7 Page Access",
        "description": "Adds sensor page access when Sensor 7 is attached to the farm.",
        "effect": "allow",
        "priority": 20,
        "features": ["sensor-page"],
        "sensor_catalogs": [SENSOR_7_NAME],
        "metadata": {"sensor_catalog_names": [SENSOR_7_NAME]},
    },
]
