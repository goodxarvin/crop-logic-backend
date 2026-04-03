# تغییرات سطح دسترسی برای فرانت

این سند توضیح می‌دهد فرانت چطور از سیستم `access_control` استفاده کند، چه `feature code` هایی وجود دارند، و plan `gold` دقیقاً چه دسترسی‌هایی می‌دهد.

## 1) API پروفایل دسترسی مزرعه

برای گرفتن دسترسی موثر هر مزرعه از این endpoint استفاده کنید:

- `GET /api/access-control/farms/{farm_uuid}/profile/`
- نیازمند `Authorization: Bearer <access_token>`

نمونه پاسخ:

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "farm_uuid": "11111111-1111-1111-1111-111111111111",
    "subscription_plan": {
      "uuid": "22222222-2222-2222-2222-222222222222",
      "code": "gold",
      "name": "Gold"
    },
    "features": {
      "greenhouse-dashboard": {
        "enabled": true,
        "type": "page",
        "name": "Greenhouse Dashboard",
        "description": "",
        "metadata": {},
        "source": "gold-full-access"
      },
      "sensor-page": {
        "enabled": true,
        "type": "page",
        "name": "صفحه سنسور",
        "description": "",
        "metadata": {},
        "source": "sensor-7-page-access"
      }
    },
    "groups": {
      "pages": {
        "greenhouse-dashboard": {
          "enabled": true,
          "type": "page",
          "name": "Greenhouse Dashboard",
          "description": "",
          "metadata": {},
          "source": "gold-full-access"
        }
      }
    },
    "matched_rules": [
      {
        "code": "gold-full-access",
        "name": "Gold Full Access",
        "effect": "allow",
        "priority": 10
      },
      {
        "code": "sensor-7-page-access",
        "name": "Sensor 7 Page Access",
        "effect": "allow",
        "priority": 20
      }
    ],
    "resolved_from_profile": true
  }
}
```

## 2) رفتار پیش‌فرض plan

- plan پیش‌فرض فارم‌های جدید: `gold`
- اگر فرانت هنگام ساخت فارم `subscription_plan_uuid` نفرستد، backend به‌صورت پیش‌فرض plan `gold` را ست می‌کند.
- بنابراین در اکثر سناریوهای فعلی، کاربر جدید بعد از ساخت فارم باید دسترسی‌های Gold را داشته باشد.

## 3) feature code ها

این `code` ها کلید اصلی برای بررسی دسترسی در فرانت هستند:

- `dashboards` : سکشن داشبوردها
- `data-section` : سکشن بخش داده‌ها
- `water-data` : صفحه دیتاهای آب
- `soil-information` : صفحه اطلاعات خاک
- `crop-zoning` : صفحه زون‌بندی کشت
- `simulator` : سکشن شبیه‌ساز
- `plant-growth-simulator` : صفحه شبیه‌ساز رشد گیاه
- `recommendations` : سکشن توصیه‌ها
- `irrigation-recommendation` : صفحه توصیه آبیاری
- `fertilization-recommendation` : صفحه توصیه کوددهی
- `smart-assistant` : سکشن دستیار هوشمند
- `farm-ai-assistant` : صفحه دستیار هوشمند مزرعه
- `pest-detection` : صفحه تشخیص آفات گیاهی
- `sensor-page` : صفحه سنسور
- `greenhouse-dashboard` : صفحه/داشبورد گلخانه

## 4) دسترسی‌های plan `gold`

اگر `subscription_plan.code === "gold"` باشد، این featureها باید فعال باشند:

- `dashboards`
- `data-section`
- `water-data`
- `soil-information`
- `crop-zoning`
- `simulator`
- `plant-growth-simulator`
- `recommendations`
- `irrigation-recommendation`
- `fertilization-recommendation`
- `smart-assistant`
- `farm-ai-assistant`
- `pest-detection`
- `greenhouse-dashboard`

## 5) قانون سنسور

یک rule جدا هم برای سنسور تعریف شده است:

- rule code: `sensor-7-page-access`
- شرط: مزرعه سنسور `Sensor 7 - Soil Moisture Sensor v1.2` را داشته باشد
- نتیجه: feature `sensor-page` فعال می‌شود

پس برای نمایش صفحه سنسور بهتر است فقط این را چک کنید:

- `features["sensor-page"]?.enabled === true`

و لازم نیست منطق نام سنسور را داخل فرانت تکرار کنید.

## 6) source و matched_rules یعنی چه؟

- `features[code].source` نشان می‌دهد این دسترسی از کدام rule آمده است.
- `matched_rules` لیست ruleهایی است که روی این مزرعه match شده‌اند.
- برای UI معمولی معمولاً فقط `enabled` کافی است.
- برای debug یا پنل ادمین، `source` و `matched_rules` مفید هستند.

## 7) گارد دسترسی روی APIها

علاوه بر `IsAuthenticated`، گارد مبتنی بر feature هم اضافه شده است.  
اگر API نیازمند یک feature خاص باشد و آن feature برای مزرعه فعال نباشد، پاسخ:

- `403 Forbidden`

نمونه:

```json
{
  "detail": "Access to feature `greenhouse-dashboard` is denied."
}
```

## 8) APIهایی که فعلاً به feature وصل شده‌اند

فعلاً این endpointها نیازمند feature `greenhouse-dashboard` هستند:

- `GET /api/farm-dashboard/`
- `GET /api/farm-dashboard-config/`
- `PATCH /api/farm-dashboard-config/`

نکته:

- در این endpointها باید `farm_uuid` معتبر و متعلق به همان کاربر ارسال شود.

## 9) پیشنهاد پیاده‌سازی در فرانت

- بعد از انتخاب مزرعه، یک‌بار `access profile` را fetch کنید.
- نمایش منوها، سکشن‌ها و صفحه‌ها را با `features[feature_code].enabled` کنترل کنید.
- اگر کاربر مستقیم وارد صفحه شد و backend `403` داد، صفحه `عدم دسترسی` یا fallback مناسب نمایش دهید.
- در سوئیچ مزرعه، access profile را دوباره بگیرید.
- منبع نهایی حقیقت همیشه backend است، نه فقط hide/show در UI.

## 10) الگوی پیشنهادی در کد فرانت

نمونه:

```ts
const canAccess = (profile: any, featureCode: string) => {
  return profile?.features?.[featureCode]?.enabled === true;
};

const canShowDashboard = canAccess(profile, "greenhouse-dashboard");
const canShowSensorPage = canAccess(profile, "sensor-page");
const canShowPestDetection = canAccess(profile, "pest-detection");
```

## 11) جمع‌بندی قرارداد فرانت

- کلید پایدار بررسی: `feature code`
- منبع معتبر: `GET /api/access-control/farms/{farm_uuid}/profile/`
- تصمیم UI: بر اساس `features[code].enabled`
- تصمیم نهایی backend: بر اساس ruleهای access control
