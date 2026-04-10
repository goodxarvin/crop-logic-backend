ARM_ALERTS_TRACKER = {
    "totalAlerts": 3,
    "radialBarValue": 30,
    "alertStats": [
        {
            "title": "کمبود آب",
            "count": "2",
            "avatarColor": "error",
            "avatarIcon": "tabler-droplet-half-2",
        },
        {
            "title": "ریسک قارچی",
            "count": "1",
            "avatarColor": "warning",
            "avatarIcon": "tabler-mushroom",
        },
        {
            "title": "هشدار یخبندان",
            "count": "0",
            "avatarColor": "info",
            "avatarIcon": "tabler-snowflake",
        },
    ],
}

FARM_ALERTS_TIMELINE = {
    "alerts": [
        {
            "title": "ریسک کمبود آب",
            "description": "رطوبت خاک در عمق ۱۰ سانتی‌متر (۴۲٪) کمتر از حد بهینه است. پیش‌بینی: در صورت عدم آبیاری، تنش طی ۲ تا ۳ روز. توصیه: آبیاری ظرف ۲۴ ساعت.",
            "time": "۱۵ دقیقه پیش",
            "color": "warning",
        },
        {
            "title": "ریسک بیماری قارچی",
            "description": "رطوبت بالا (۶۵٪) و دمای ۲۴ درجه شرایط مساعد برای رشد قارچ. استفاده از قارچ‌کش پیشگیرانه یا کاهش آبیاری را در نظر بگیرید.",
            "time": "۱ ساعت پیش",
            "color": "error",
        },
        {
            "title": "پیشنهاد آبیاری",
            "description": "بازه بهینه آبیاری: ۶:۰۰ تا ۸:۰۰ صبح. حجم پیشنهادی: ۴۵۰ مترمکعب برای زون آ. بهبود راندمان مورد انتظار: ۱۲٪.",
            "time": "۲ ساعت پیش",
            "color": "info",
        },
        {
            "title": "بررسی شوری خاک",
            "description": "مقدار هدایت الکتریکی ۱/۲ dS/m در محدوده مجاز است. نیازی به اقدام نیست. بررسی بعدی توصیه می‌شود ظرف ۵ روز.",
            "time": "۴ ساعت پیش",
            "color": "success",
        },
    ]
}

ANOMALY_DETECTION_CARD = {
    "anomalies": [
        {
            "sensor": "رطوبت خاک زون ۳",
            "value": "38%",
            "expected": "45-65%",
            "deviation": "-12%",
            "severity": "warning",
        },
        {
            "sensor": "pH بخش ۲",
            "value": "5.2",
            "expected": "6.0-7.0",
            "deviation": "-0.8",
            "severity": "error",
        },
    ]
}

RECOMMENDATIONS_LIST = {
    "recommendations": [
        {
            "title": "آبیاری: ۶:۰۰ تا ۸:۰۰ صبح",
            "subtitle": "۴۵۰ مترمکعب برای زون آ. بدون آبیاری، عملکرد ممکن است حدود ۸٪ کاهش یابد.",
            "avatarIcon": "tabler-droplet",
            "avatarColor": "primary",
        },
        {
            "title": "کود: NPK 20-20-20",
            "subtitle": "اعمال ۲۵ کیلوگرم در هکتار ظرف ۷ روز. کمبود نیتروژن فعلی در بخش ۲.",
            "avatarIcon": "tabler-leaf",
            "avatarColor": "success",
        },
        {
            "title": "قارچ‌کش: پیشگیرانه",
            "subtitle": "رطوبت و دما مساعد قارچ. سمپاشی بر پایه مس را در نظر بگیرید.",
            "avatarIcon": "tabler-mushroom",
            "avatarColor": "warning",
        },
        {
            "title": "بازه برداشت: ۱۲ تا ۱۸ اکتبر",
            "subtitle": "اوج رسیدگی حدود ۱۵ اکتبر. نیروی کار را متناسب برنامه‌ریزی کنید.",
            "avatarIcon": "tabler-calendar-event",
            "avatarColor": "info",
        },
    ]
}
