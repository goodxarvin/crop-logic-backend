"""
Static mock data for Pest Detection API.
No database, no dynamic values. Used for analyze and risk-summary endpoint responses.
"""

ANALYZE_RESPONSE_DATA = {
    "pest": "شپشک",
    "confidence": 92,
    "description": "حشرات کوچک مکنده شیره که باعث پیچ خوردگی برگ می‌شوند.",
    "treatment": "یک بار در هفته از اسپری روغن نیم استفاده کنید.",
}

RISK_SUMMARY_RESPONSE_DATA = {
    "disease_risk": {
        "id": "disease_risk",
        "title": "ریسک بیماری",
        "subtitle": "۷ روز اخیر",
        "stats": "پایین",
        "avatarColor": "success",
        "avatarIcon": "tabler-bug",
        "chipText": "5%",
        "chipColor": "success",
        "details": {
            "risk_level": "low",
            "risk_percentage": 5,
            "detected_diseases": [],
            "last_assessed_at": "2025-07-10T06:00:00Z",
            "recommendation": "شرایط فعلی مناسب است. پایش هفتگی توصیه می‌شود.",
        },
    },
    "pest_risk": {
        "id": "pest_risk",
        "title": "ریسک آفات",
        "subtitle": "پیش‌بینی هوشمند",
        "stats": "15%",
        "avatarColor": "warning",
        "avatarIcon": "tabler-bug-off",
        "chipText": "تحت نظر",
        "chipColor": "warning",
        "details": {
            "risk_level": "moderate",
            "risk_percentage": 15,
            "detected_pests": [
                {
                    "name": "شپشک",
                    "confidence": 0.72,
                    "affected_area_percent": 8,
                }
            ],
            "last_assessed_at": "2025-07-10T06:00:00Z",
            "recommendation": "بازرسی مزرعه هر ۳ روز یک بار انجام شود. در صورت افزایش، اسپری روغن نیم توصیه می‌شود.",
        },
    },
}
