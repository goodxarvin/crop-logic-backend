AVG_SOIL_MOISTURE = {
    "id": "avg_soil_moisture",
    "title": "میانگین رطوبت خاک",
    "subtitle": "سنسور 7 در 1 خاک",
    "stats": "45%",
    "avatarColor": "primary",
    "avatarIcon": "tabler-droplet",
    "chipText": "متوسط",
    "chipColor": "warning",
}


SENSOR_VALUES_LIST = {
    "sensor": {
        "name": "سنسور 7 در 1 خاک",
        "physicalDeviceUuid": None,
        "sensorCatalogCode": "sensor-7-in-1",
        "updatedAt": None,
    },
    "sensors": [
        {
            "id": "soil_moisture",
            "title": "45%",
            "subtitle": "رطوبت خاک",
            "trendNumber": 1.5,
            "trend": "positive",
            "unit": "%",
        },
        {
            "id": "soil_temperature",
            "title": "22.5°C",
            "subtitle": "دمای خاک",
            "trendNumber": 0.8,
            "trend": "positive",
            "unit": "°C",
        },
        {
            "id": "soil_ph",
            "title": "6.8",
            "subtitle": "pH خاک",
            "trendNumber": 0.1,
            "trend": "positive",
            "unit": "pH",
        },
        {
            "id": "electrical_conductivity",
            "title": "1.2 dS/m",
            "subtitle": "هدایت الکتریکی",
            "trendNumber": -0.1,
            "trend": "negative",
            "unit": "dS/m",
        },
        {
            "id": "nitrogen",
            "title": "30 mg/kg",
            "subtitle": "نیتروژن",
            "trendNumber": 2.0,
            "trend": "positive",
            "unit": "mg/kg",
        },
        {
            "id": "phosphorus",
            "title": "15 mg/kg",
            "subtitle": "فسفر",
            "trendNumber": 1.0,
            "trend": "positive",
            "unit": "mg/kg",
        },
        {
            "id": "potassium",
            "title": "20 mg/kg",
            "subtitle": "پتاسیم",
            "trendNumber": -1.0,
            "trend": "negative",
            "unit": "mg/kg",
        },
    ],
}


SENSOR_RADAR_CHART = {
    "labels": ["رطوبت", "دما", "pH", "EC", "نیتروژن", "فسفر", "پتاسیم"],
    "series": [
        {"name": "اکنون", "data": [82, 76, 90, 72, 68, 62, 70]},
        {"name": "هدف", "data": [100, 100, 100, 100, 100, 100, 100]},
    ],
}


SENSOR_COMPARISON_CHART = {
    "currentValue": 45,
    "vsLastWeek": "+4.7%",
    "vsLastWeekValue": 4.7,
    "categories": ["08:00", "10:00", "12:00", "14:00", "16:00", "18:00", "20:00"],
    "series": [
        {"name": "رطوبت خاک", "data": [42, 44, 45, 47, 46, 45, 45]},
        {"name": "بازه هدف", "data": [55, 55, 55, 55, 55, 55, 55]},
    ],
}


ANOMALY_DETECTION_CARD = {
    "anomalies": [
        {
            "sensor": "هدایت الکتریکی",
            "value": "1.2 dS/m",
            "expected": "0.8-1.1 dS/m",
            "deviation": "+0.1 dS/m",
            "severity": "warning",
        }
    ]
}


SOIL_MOISTURE_HEATMAP = {
    "zones": ["سنسور 7 در 1 خاک"],
    "hours": ["08:00", "10:00", "12:00", "14:00", "16:00", "18:00", "20:00"],
    "series": [
        {
            "name": "سنسور 7 در 1 خاک",
            "data": [
                {"x": "08:00", "y": 42},
                {"x": "10:00", "y": 44},
                {"x": "12:00", "y": 45},
                {"x": "14:00", "y": 47},
                {"x": "16:00", "y": 46},
                {"x": "18:00", "y": 45},
                {"x": "20:00", "y": 45},
            ],
        }
    ],
}

