GOLD_PLAN_CODE = "gold"
SENSOR_7_NAME = "Sensor 7 - Soil Moisture Sensor v1.2"
SENSOR_7_CODE = "sensor_7_soil_moisture_sensor_v1_2"


DEFAULT_SUBSCRIPTION_PLANS = [
    {
        "code": "gold",
        "name": "Gold",
        "description": "Default premium subscription plan with full CropLogic access.",
        "metadata": {"is_default": True},
    },
]


DEFAULT_ACCESS_FEATURES = [
    {"code": "dashboards", "name": "داشبوردها", "feature_type": "section", "default_enabled": True},
    {"code": "data-section", "name": "بخش داده ها", "feature_type": "section", "default_enabled": True},
    {"code": "water-data", "name": "دیتاهای آب", "feature_type": "page", "default_enabled": True},
    {"code": "soil-information", "name": "اطلاعات خاک", "feature_type": "page", "default_enabled": True},
    {"code": "crop-zoning", "name": "زون بندی کشت", "feature_type": "page", "default_enabled": True},
    {"code": "simulator", "name": "شبیه ساز", "feature_type": "section", "default_enabled": True},
    {"code": "plant-growth-simulator", "name": "شبیه ساز رشد گیاه", "feature_type": "page", "default_enabled": True},
    {"code": "recommendations", "name": "توصیه ها", "feature_type": "section", "default_enabled": True},
    {"code": "irrigation-recommendation", "name": "توصیه آبیاری", "feature_type": "page", "default_enabled": True},
    {"code": "fertilization-recommendation", "name": "توصیه کوددهی", "feature_type": "page", "default_enabled": True},
    {"code": "smart-assistant", "name": "دستیار هوشمند", "feature_type": "section", "default_enabled": True},
    {"code": "farm-ai-assistant", "name": "دستیار هوشمند مزرعه", "feature_type": "page", "default_enabled": True},
    {"code": "pest-detection", "name": "تشخیص آفات گیاهی", "feature_type": "page", "default_enabled": True},
    {"code": "sensor-page", "name": "صفحه سنسور", "feature_type": "page", "default_enabled": True},
    {"code": "greenhouse-dashboard", "name": "Greenhouse Dashboard", "feature_type": "page", "default_enabled": True},
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
        "sensor_catalog_codes": [SENSOR_7_CODE],
        "metadata": {"sensor_catalog_codes": [SENSOR_7_CODE]},
    },
]
