# مستندات APIهای توصیه و تشخیص

این سند سه گروه API را شرح می‌دهد: **توصیه آبیاری**، **تشخیص آفت** و **توصیه کوددهی**. همهٔ پاسخ‌ها در حال حاضر از دادهٔ ثابت (mock) برگردانده می‌شوند و پارامترهای ورودی در پاسخ استفاده نمی‌شوند.

**پایهٔ آدرس API:** `/api/`

**قالب کلی پاسخ:**  
`{"status": "success", "data": <payload>}` — فقط با کد وضعیت HTTP 200.

---

## ۱. توصیه آبیاری (Irrigation Recommendation)

**پیشوند:** `api/irrigation-recommendation/`

### ۱.۱ دریافت تنظیمات (Config)

- **متد:** `GET`
- **آدرس:** `api/irrigation-recommendation/config/`
- **هدف:** برگرداندن اطلاعات مزرعه و لیست گزینه‌های محصول برای فرم توصیه آبیاری (هنگام بارگذاری صفحه).
- **ورودی:** ندارد. پارامترهای query خوانده یا استفاده نمی‌شوند.

**نمونه پاسخ:**

```json
{
  "status": "success",
  "data": {
    "farmInfo": {
      "soilType": "Loamy",
      "waterQuality": "Medium EC",
      "climateZone": "Temperate"
    },
    "cropOptions": [
      {"id": "wheat", "labelKey": "wheat", "icon": "tabler-wheat"},
      {"id": "corn", "labelKey": "corn", "icon": "tabler-plant-2"},
      {"id": "cotton", "labelKey": "cotton", "icon": "tabler-flower"},
      {"id": "saffron", "labelKey": "saffron", "icon": "tabler-flower-2"},
      {"id": "canola", "labelKey": "canola", "icon": "tabler-leaf"},
      {"id": "vegetables", "labelKey": "vegetables", "icon": "tabler-carrot"}
    ]
  }
}
```

| فیلد | نوع | توضیح |
|------|-----|--------|
| `farmInfo.soilType` | string | نوع خاک |
| `farmInfo.waterQuality` | string | کیفیت آب (مثلاً EC) |
| `farmInfo.climateZone` | string | منطقه اقلیمی |
| `cropOptions` | array | لیست محصولات: `id`, `labelKey`, `icon` |

---

### ۱.۲ دریافت توصیه آبیاری (Recommend)

- **متد:** `POST`
- **آدرس:** `api/irrigation-recommendation/recommend/`
- **هدف:** برگرداندن یک برنامهٔ آبیاری ثابت (تعداد در هفته، مدت، بهترین زمان، رطوبت، هشدار).
- **ورودی (بدن درخواست، اختیاری):** می‌توانید JSON با فیلدهایی مثل `crop_id`, `soilType`, `waterQuality`, `climateZone` بفرستید؛ در پاسخ فعلی استفاده نمی‌شوند.
- **CSRF:** این endpoint از CSRF معاف است (برای فراخوانی از فرانت بدون توکن).

**نمونه پاسخ:**

```json
{
  "status": "success",
  "data": {
    "plan": {
      "frequencyPerWeek": 4,
      "durationMinutes": 45,
      "bestTimeOfDay": "05:00 - 07:00",
      "moistureLevel": 72,
      "warning": "Avoid irrigation during midday hours in the coming week due to forecasted high temperatures."
    }
  }
}
```

| فیلد | نوع | توضیح |
|------|-----|--------|
| `plan.frequencyPerWeek` | number | تعداد آبیاری در هفته |
| `plan.durationMinutes` | number | مدت هر نوبت (دقیقه) |
| `plan.bestTimeOfDay` | string | بهترین بازه زمانی روز |
| `plan.moistureLevel` | number | سطح رطوبت هدف (درصد) |
| `plan.warning` | string | هشدار یا توصیه اضافه |

---

## ۲. تشخیص آفت (Pest Detection)

**پیشوند:** `api/pest-detection/`

### ۲.۱ تحلیل تصویر (Analyze)

- **متد:** `POST`
- **آدرس:** `api/pest-detection/analyze/`
- **هدف:** برگرداندن نتیجهٔ ثابت تشخیص آفت (نام آفت، اطمینان، توضیح، درمان) — برای زمانی که کاربر تصویر گیاه را آپلود و درخواست تحلیل می‌کند.
- **ورودی (بدن درخواست، اختیاری):** JSON یا form-data (مثلاً شامل `image` یا `file`). در پاسخ فعلی استفاده نمی‌شود.
- **CSRF:** این endpoint از CSRF معاف است.

**نمونه پاسخ:**

```json
{
  "status": "success",
  "data": {
    "pest": "شپشک",
    "confidence": 92,
    "description": "حشرات کوچک مکنده شیره که باعث پیچ خوردگی برگ می‌شوند.",
    "treatment": "یک بار در هفته از اسپری روغن نیم استفاده کنید."
  }
}
```

| فیلد | نوع | توضیح |
|------|-----|--------|
| `pest` | string | نام آفت |
| `confidence` | number | درصد اطمینان (۰–۱۰۰) |
| `description` | string | توضیح کوتاه آفت |
| `treatment` | string | توصیه درمان |

---

## ۳. توصیه کوددهی (Fertilization Recommendation)

**پیشوند:** `api/fertilization-recommendation/`

### ۳.۱ دریافت تنظیمات (Config)

- **متد:** `GET`
- **آدرس:** `api/fertilization-recommendation/config/`
- **هدف:** برگرداندن دادهٔ مزرعه، مراحل رشد و گزینه‌های محصول برای فرم توصیه کوددهی (هنگام بارگذاری صفحه).
- **ورودی:** ندارد.

**نمونه پاسخ:**

```json
{
  "status": "success",
  "data": {
    "farmData": {
      "soilType": "Loamy",
      "organicMatter": "Medium (2.5%)",
      "waterEC": "1.2 dS/m"
    },
    "growthStages": [
      {"id": "prePlanting", "icon": "tabler-seedling"},
      {"id": "earlyGrowth", "icon": "tabler-leaf"},
      {"id": "flowering", "icon": "tabler-flower"},
      {"id": "fruiting", "icon": "tabler-apple"},
      {"id": "postHarvest", "icon": "tabler-basket"}
    ],
    "cropOptions": [
      {"id": "wheat", "labelKey": "wheat", "icon": "tabler-wheat"},
      {"id": "corn", "labelKey": "corn", "icon": "tabler-plant-2"},
      {"id": "cotton", "labelKey": "cotton", "icon": "tabler-flower"},
      {"id": "saffron", "labelKey": "saffron", "icon": "tabler-flower-2"},
      {"id": "canola", "labelKey": "canola", "icon": "tabler-leaf"},
      {"id": "vegetables", "labelKey": "vegetables", "icon": "tabler-carrot"}
    ]
  }
}
```

| فیلد | نوع | توضیح |
|------|-----|--------|
| `farmData.soilType` | string | نوع خاک |
| `farmData.organicMatter` | string | ماده آلی خاک |
| `farmData.waterEC` | string | EC آب |
| `growthStages` | array | مراحل رشد: `id`, `icon` |
| `cropOptions` | array | لیست محصولات: `id`, `labelKey`, `icon` |

---

### ۳.۲ دریافت توصیه کوددهی (Recommend)

- **متد:** `POST`
- **آدرس:** `api/fertilization-recommendation/recommend/`
- **هدف:** برگرداندن یک برنامهٔ کوددهی ثابت (نسبت NPK، مقدار در هکتار، روش و فاصله مصرف، استدلال).
- **ورودی (بدن درخواست، اختیاری):** JSON با فیلدهایی مثل `crop_id`, `growth_stage`, `soilType`, `organicMatter`, `waterEC`. در پاسخ فعلی استفاده نمی‌شوند.
- **CSRF:** این endpoint از CSRF معاف است.

**نمونه پاسخ:**

```json
{
  "status": "success",
  "data": {
    "plan": {
      "npkRatio": "20-20-20 (NPK)",
      "amountPerHectare": "150 kg/ha",
      "applicationMethod": "Foliar spray + soil broadcast",
      "applicationInterval": "Every 14 days",
      "reasoning": "Your loamy soil with medium organic matter (2.5%) provides good nutrient retention. Water EC of 1.2 dS/m indicates low salinity—suitable for most crops. At the flowering stage, increased phosphorus supports bloom development. We recommend a balanced NPK to maintain nitrogen for vegetative growth while boosting phosphorous for flowering."
    }
  }
}
```

| فیلد | نوع | توضیح |
|------|-----|--------|
| `plan.npkRatio` | string | نسبت NPK پیشنهادی |
| `plan.amountPerHectare` | string | مقدار مصرف در هکتار |
| `plan.applicationMethod` | string | روش مصرف (مثلاً محلول‌پاشی، خاکی) |
| `plan.applicationInterval` | string | فاصله بین مصرف |
| `plan.reasoning` | string | توضیح/استدلال توصیه |

---

## خلاصه Endpointها

| ماژول | متد | Endpoint |
|--------|------|----------|
| Irrigation | GET | `/api/irrigation-recommendation/config/` |
| Irrigation | POST | `/api/irrigation-recommendation/recommend/` |
| Pest Detection | POST | `/api/pest-detection/analyze/` |
| Fertilization | GET | `/api/fertilization-recommendation/config/` |
| Fertilization | POST | `/api/fertilization-recommendation/recommend/` |

---

**توجه:** در نسخهٔ فعلی هیچ پردازش، اعتبارسنجی یا استفاده از پارامترهای ورودی در پاسخ انجام نمی‌شود؛ همهٔ خروجی‌ها از دادهٔ ثابت (mock) هستند.
