"""
Static mock data for Crop Zoning API.
Matches CROP_ZONING_APIS.md. No database, no dynamic values.
"""

# ---------------------------------------------------------------------------
# GET /api/crop-zoning/area/
# منطقهٔ ثابت — کاربر امکان رسم ندارد
# ---------------------------------------------------------------------------

AREA_RESPONSE_DATA = {
    "area": {
        "type": "Feature",
        "properties": {},
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [51.38, 35.68],
                    [51.405, 35.672],
                    [51.41, 35.695],
                    [51.385, 35.71],
                    [51.365, 35.688],
                    [51.38, 35.68],
                ]
            ],
        },
    }
}

# ---------------------------------------------------------------------------
# GET /api/crop-zoning/products/
# ---------------------------------------------------------------------------

PRODUCTS_RESPONSE_DATA = {
    "products": [
        {"id": "wheat", "label": "گندم", "color": "#6bcb77"},
        {"id": "canola", "label": "کلزا", "color": "#ffd93d"},
        {"id": "saffron", "label": "زعفران", "color": "#9b59b6"},
    ]
}

# ---------------------------------------------------------------------------
# POST /api/crop-zoning/zones/initial/
# دیتای اولیه برای نقشه و هاور/tooltip — بدون reason و criteria
# ---------------------------------------------------------------------------

ZONES_INITIAL_RESPONSE_DATA = {
    "total_area_hectares": 23.45,
    "total_area_sqm": 234500,
    "zone_count": 3,
    "zones": [
        {
            "zoneId": "zone-0",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [51.38, 35.68],
                        [51.3815, 35.68],
                        [51.3815, 35.6815],
                        [51.38, 35.6815],
                        [51.38, 35.68],
                    ]
                ],
            },
            "crop": "wheat",
            "matchPercent": 85,
            "waterNeed": "۴۵۰۰-۵۵۰۰ m³/ha",
            "estimatedProfit": "۱۵-۲۵ میلیون/هکتار",
        },
        {
            "zoneId": "zone-1",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [51.3815, 35.68],
                        [51.383, 35.68],
                        [51.383, 35.6815],
                        [51.3815, 35.6815],
                        [51.3815, 35.68],
                    ]
                ],
            },
            "crop": "canola",
            "matchPercent": 78,
            "waterNeed": "۵۰۰۰-۶۰۰۰ m³/ha",
            "estimatedProfit": "۲۰-۳۵ میلیون/هکتار",
        },
        {
            "zoneId": "zone-2",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [51.38, 35.6815],
                        [51.3815, 35.6815],
                        [51.3815, 35.683],
                        [51.38, 35.683],
                        [51.38, 35.6815],
                    ]
                ],
            },
            "crop": "saffron",
            "matchPercent": 92,
            "waterNeed": "۳۰۰۰-۴۰۰۰ m³/ha",
            "estimatedProfit": "۵۰-۱۵۰ میلیون/هکتار",
        },
    ],
}

# ---------------------------------------------------------------------------
# POST /api/crop-zoning/zones/water-need/
# نیاز آبی هر منطقه برای لایهٔ نیاز آبی
# ---------------------------------------------------------------------------

ZONES_WATER_NEED_RESPONSE_DATA = {
    "zones": [
        {
            "zoneId": "zone-0",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [51.38, 35.68],
                        [51.3815, 35.68],
                        [51.3815, 35.6815],
                        [51.38, 35.6815],
                        [51.38, 35.68],
                    ]
                ],
            },
            "level": "medium",
            "value": "۴۵۰۰-۵۵۰۰ m³/ha",
            "color": "#0ea5e9",
        },
        {
            "zoneId": "zone-1",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [51.3815, 35.68],
                        [51.383, 35.68],
                        [51.383, 35.6815],
                        [51.3815, 35.6815],
                        [51.3815, 35.68],
                    ]
                ],
            },
            "level": "high",
            "value": "۵۰۰۰-۶۰۰۰ m³/ha",
            "color": "#0369a1",
        },
        {
            "zoneId": "zone-2",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [51.38, 35.6815],
                        [51.3815, 35.6815],
                        [51.3815, 35.683],
                        [51.38, 35.683],
                        [51.38, 35.6815],
                    ]
                ],
            },
            "level": "low",
            "value": "۳۰۰۰-۴۰۰۰ m³/ha",
            "color": "#7dd3fc",
        },
    ]
}

# ---------------------------------------------------------------------------
# POST /api/crop-zoning/zones/soil-quality/
# کیفیت خاک هر منطقه برای لایهٔ کیفیت خاک
# ---------------------------------------------------------------------------

ZONES_SOIL_QUALITY_RESPONSE_DATA = {
    "zones": [
        {
            "zoneId": "zone-0",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [51.38, 35.68],
                        [51.3815, 35.68],
                        [51.3815, 35.6815],
                        [51.38, 35.6815],
                        [51.38, 35.68],
                    ]
                ],
            },
            "level": "high",
            "score": 88,
            "color": "#22c55e",
        },
        {
            "zoneId": "zone-1",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [51.3815, 35.68],
                        [51.383, 35.68],
                        [51.383, 35.6815],
                        [51.3815, 35.6815],
                        [51.3815, 35.68],
                    ]
                ],
            },
            "level": "medium",
            "score": 62,
            "color": "#eab308",
        },
        {
            "zoneId": "zone-2",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [51.38, 35.6815],
                        [51.3815, 35.6815],
                        [51.3815, 35.683],
                        [51.38, 35.683],
                        [51.38, 35.6815],
                    ]
                ],
            },
            "level": "high",
            "score": 95,
            "color": "#22c55e",
        },
    ]
}

# ---------------------------------------------------------------------------
# POST /api/crop-zoning/zones/cultivation-risk/
# ریسک کشت هر منطقه برای لایهٔ ریسک کشت
# ---------------------------------------------------------------------------

ZONES_CULTIVATION_RISK_RESPONSE_DATA = {
    "zones": [
        {
            "zoneId": "zone-0",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [51.38, 35.68],
                        [51.3815, 35.68],
                        [51.3815, 35.6815],
                        [51.38, 35.6815],
                        [51.38, 35.68],
                    ]
                ],
            },
            "level": "low",
            "color": "#22c55e",
        },
        {
            "zoneId": "zone-1",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [51.3815, 35.68],
                        [51.383, 35.68],
                        [51.383, 35.6815],
                        [51.3815, 35.6815],
                        [51.3815, 35.68],
                    ]
                ],
            },
            "level": "medium",
            "color": "#f59e0b",
        },
        {
            "zoneId": "zone-2",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [51.38, 35.6815],
                        [51.3815, 35.6815],
                        [51.3815, 35.683],
                        [51.38, 35.683],
                        [51.38, 35.6815],
                    ]
                ],
            },
            "level": "low",
            "color": "#22c55e",
        },
    ]
}

# ---------------------------------------------------------------------------
# GET /api/crop-zoning/zones/:zoneId/details/
# دیتای تکمیلی برای پنل جزئیات — شامل reason و criteria
# منطبق با createZonedGrid و MOCK_AREA_GEOJSON
# ---------------------------------------------------------------------------

ZONE_DETAILS_BY_ID = {
    "zone-0": {
        "zoneId": "zone-0",
        "crop": "wheat",
        "matchPercent": 85,
        "waterNeed": "۴۵۰۰-۵۵۰۰ m³/ha",
        "estimatedProfit": "۱۵-۲۵ میلیون/هکتار",
        "reason": "دمای مناسب، خاک حاصلخیز، دسترسی به آب کافی",
        "criteria": [
            {"name": "دما", "value": 82},
            {"name": "بارش", "value": 75},
            {"name": "خاک", "value": 88},
            {"name": "آب", "value": 70},
        ],
        "area_hectares": 2.25,
    },
    "zone-1": {
        "zoneId": "zone-1",
        "crop": "canola",
        "matchPercent": 78,
        "waterNeed": "۵۰۰۰-۶۰۰۰ m³/ha",
        "estimatedProfit": "۲۰-۳۵ میلیون/هکتار",
        "reason": "شرایط اقلیمی مساعد، نیاز آبی قابل تأمین",
        "criteria": [
            {"name": "دما", "value": 75},
            {"name": "بارش", "value": 72},
            {"name": "خاک", "value": 80},
            {"name": "آب", "value": 78},
        ],
        "area_hectares": 2.25,
    },
    "zone-2": {
        "zoneId": "zone-2",
        "crop": "saffron",
        "matchPercent": 92,
        "waterNeed": "۳۰۰۰-۴۰۰۰ m³/ha",
        "estimatedProfit": "۵۰-۱۵۰ میلیون/هکتار",
        "reason": "ارتفاع و آب و هوای خشک مناسب، پتانسیل سود بالا",
        "criteria": [
            {"name": "دما", "value": 90},
            {"name": "بارش", "value": 65},
            {"name": "خاک", "value": 95},
            {"name": "آب", "value": 85},
        ],
        "area_hectares": 2.25,
    },
}
