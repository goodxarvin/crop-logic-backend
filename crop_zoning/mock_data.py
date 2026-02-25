"""
Static mock data for Crop Zoning API.
Matches API_RESPONSE_SPEC.md. No database, no dynamic values.
"""

# Response for POST optimize: GeoJSON FeatureCollection (API_RESPONSE_SPEC §1)
OPTIMIZE_ZONING_RESPONSE = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [51.38, 35.68],
                        [51.381, 35.68],
                        [51.381, 35.681],
                        [51.38, 35.681],
                        [51.38, 35.68],
                    ]
                ],
            },
            "properties": {
                "zoneId": "zone-0",
                "crop": "wheat",
                "matchPercent": 78,
                "waterNeed": "۴۵۰۰-۵۵۰۰ m³/ha",
                "estimatedProfit": "۱۵-۲۵ میلیون/هکتار",
                "reason": "دمای مناسب، خاک حاصلخیز، دسترسی به آب کافی",
                "criteria": [
                    {"name": "دما", "value": 85},
                    {"name": "بارش", "value": 72},
                    {"name": "خاک", "value": 80},
                    {"name": "آب", "value": 65},
                ],
            },
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [51.381, 35.68],
                        [51.382, 35.68],
                        [51.382, 35.681],
                        [51.381, 35.681],
                        [51.381, 35.68],
                    ]
                ],
            },
            "properties": {
                "zoneId": "zone-1",
                "crop": "canola",
                "matchPercent": 82,
                "waterNeed": "۳۵۰۰-۴۵۰۰ m³/ha",
                "estimatedProfit": "۲۰-۳۰ میلیون/هکتار",
                "reason": "بارش کافی، خاک با بافت مناسب",
                "criteria": [
                    {"name": "دما", "value": 70},
                    {"name": "بارش", "value": 88},
                    {"name": "خاک", "value": 75},
                    {"name": "آب", "value": 90},
                ],
            },
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [51.382, 35.68],
                        [51.40, 35.68],
                        [51.40, 35.681],
                        [51.382, 35.681],
                        [51.382, 35.68],
                    ]
                ],
            },
            "properties": {
                "zoneId": "zone-2",
                "crop": "saffron",
                "matchPercent": 65,
                "waterNeed": "۲۵۰۰-۳۵۰۰ m³/ha",
                "estimatedProfit": "۸۰-۱۲۰ میلیون/هکتار",
                "reason": "آب و هوای خشک و سرد مناسب زعفران",
                "criteria": [
                    {"name": "دما", "value": 60},
                    {"name": "بارش", "value": 55},
                    {"name": "خاک", "value": 85},
                    {"name": "آب", "value": 50},
                ],
            },
        },
    ],
}

# Response for GET initial region: GeoJSON Feature with Polygon (API_RESPONSE_SPEC §2)
INITIAL_REGION_RESPONSE = {
    "type": "Feature",
    "properties": {},
    "geometry": {
        "type": "Polygon",
        "coordinates": [
            [
                [51.38, 35.68],
                [51.40, 35.68],
                [51.40, 35.70],
                [51.38, 35.70],
                [51.38, 35.68],
            ]
        ],
    },
}
