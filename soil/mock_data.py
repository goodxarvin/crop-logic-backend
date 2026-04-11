AVG_SOIL_MOISTURE = {
    "id": "avg_soil_moisture",
    "title": "میانگین رطوبت خاک",
    "subtitle": "کل مزرعه",
    "stats": "65%",
    "avatarColor": "primary",
    "avatarIcon": "tabler-plant-2",
    "chipText": "بهینه",
    "chipColor": "success",
}


SENSOR_RADAR_CHART = {
    "labels": ["دما", "رطوبت", "pH", "هدایت الکتریکی", "نور", "باد"],
    "series": [
        {"name": "امروز", "data": [75, 65, 80, 70, 85, 60]},
        {"name": "ایده آل", "data": [80, 70, 75, 75, 90, 50]},
    ],
}


SENSOR_COMPARISON_CHART = {
    "currentValue": 48,
    "vsLastWeek": "+5%",
    "vsLastWeekValue": 5,
    "categories": ["دوشنبه", "سه شنبه", "چهارشنبه", "پنج شنبه", "جمعه", "شنبه", "یکشنبه"],
    "series": [
        {"name": "امروز", "data": [42, 45, 48, 52, 50, 48, 46]},
        {"name": "هفته قبل", "data": [38, 40, 42, 45, 43, 40, 38]},
    ],
}


ANOMALY_DETECTION_CARD = {
    "anomalies": [
        {
            "sensor": "رطوبت خاک زون 3",
            "value": "38%",
            "expected": "45-65%",
            "deviation": "-12%",
            "severity": "warning",
        },
        {
            "sensor": "pH بخش 2",
            "value": "5.2",
            "expected": "6.0-7.0",
            "deviation": "-0.8",
            "severity": "error",
        },
    ]
}


SOIL_MOISTURE_HEATMAP = {
    "zones": ["زون 1", "زون 2", "زون 3", "زون 4", "زون 5", "زون 6", "زون 7"],
    "hours": ["6 ص", "8 ص", "10 ص", "12 ظ", "14 ع", "16 ع", "18 ع"],
    "series": [
        {
            "name": "زون 1",
            "data": [
                {"x": "6 ص", "y": 52},
                {"x": "8 ص", "y": 48},
                {"x": "10 ص", "y": 55},
                {"x": "12 ظ", "y": 60},
                {"x": "14 ع", "y": 58},
                {"x": "16 ع", "y": 54},
                {"x": "18 ع", "y": 50},
            ],
        },
        {
            "name": "زون 2",
            "data": [
                {"x": "6 ص", "y": 45},
                {"x": "8 ص", "y": 42},
                {"x": "10 ص", "y": 48},
                {"x": "12 ظ", "y": 52},
                {"x": "14 ع", "y": 50},
                {"x": "16 ع", "y": 47},
                {"x": "18 ع", "y": 44},
            ],
        },
    ],
}
