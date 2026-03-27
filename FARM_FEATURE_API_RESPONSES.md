# مستند پاسخ API برای فیچرهای Farm AI

این فایل، پاسخ‌های API موردنیاز برای سه فیچر زیر را یک‌جا جمع می‌کند:

- `src/app/(dashboard)/(private)/farm-ai-assistant/page.tsx`
- `src/app/(dashboard)/(private)/fertilization-recommendation/page.tsx`
- `src/app/(dashboard)/(private)/irrigation-recommendation/page.tsx`

> مبنا، پیاده‌سازی فعلی فرانت در `src/views/dashboards/farm/...` و سرویس‌های `src/libs/api/services/...` است.

---

## قرارداد کلی پاسخ‌ها

در هر سه سرویس، فرانت انتظار این wrapper را دارد:

```json
{
  "status": "success",
  "data": {}
}
```

- `status`: معمولاً `success` یا `error`
- `data`: payload اصلی که فرانت unwrap می‌کند

---

## 1) Farm AI Assistant

### صفحه

- `src/app/(dashboard)/(private)/farm-ai-assistant/page.tsx`
- کامپوننت اصلی: `src/views/dashboards/farm/farmAiAssistant/FarmAiAssistantChat.tsx`

### APIهای موردنیاز

1. `GET /api/farm-ai-assistant/context/`
2. `POST /api/farm-ai-assistant/chat/`

---

### 1.1) دریافت context مزرعه

#### Endpoint

`GET /api/farm-ai-assistant/context/`

#### Response

```json
{
  "status": "success",
  "data": {
    "soilType": "Loamy",
    "waterEC": "1.2 dS/m",
    "selectedCrop": "Tomato",
    "growthStage": "Flowering",
    "lastIrrigationStatus": "2 days ago"
  }
}
```

#### فیلدهای لازم

| فیلد | نوع | مصرف در UI |
|------|-----|------------|
| `soilType` | `string` | badge نوع خاک |
| `waterEC` | `string` | badge EC آب |
| `selectedCrop` | `string` | badge محصول انتخاب‌شده |
| `growthStage` | `string` | badge مرحله رشد |
| `lastIrrigationStatus` | `string` | badge آخرین وضعیت آبیاری |

#### نکته

اگر این API خطا بدهد، فرانت fallback داخلی دارد و toast خطا نمایش می‌دهد.

---

### 1.2) ارسال پیام به دستیار

#### Endpoint

`POST /api/farm-ai-assistant/chat/`

#### Request body

```json
{
  "content": "What is the best irrigation plan for tomato?",
  "farm_context": {
    "soilType": "Loamy",
    "waterEC": "1.2 dS/m",
    "selectedCrop": "Tomato",
    "growthStage": "Flowering",
    "lastIrrigationStatus": "2 days ago"
  },
  "conversation_id": "conv-123"
}
```

#### Response

```json
{
  "status": "success",
  "data": {
    "message_id": "msg-001",
    "conversation_id": "conv-123",
    "content": "Here is the recommended plan.",
    "sections": [
      {
        "type": "recommendation",
        "title": "Irrigation Plan",
        "icon": "droplet",
        "frequency": "3 times per week",
        "amount": "15 liters per plant",
        "timing": "Early morning",
        "expandableExplanation": "Loamy soil holds moisture well, so moderate frequency is enough."
      },
      {
        "type": "list",
        "title": "Important Notes",
        "icon": "leaf",
        "items": [
          "Avoid watering at noon",
          "Check leaf stress every two days"
        ]
      },
      {
        "type": "warning",
        "title": "Heat Alert",
        "icon": "warning",
        "content": "Increase irrigation if temperature rises above 35°C."
      }
    ]
  }
}
```

#### فیلدهای لازم در response

| فیلد | نوع | توضیح |
|------|-----|-------|
| `message_id` | `string` | id پیام assistant |
| `conversation_id` | `string` | برای ادامه چت در پیام‌های بعدی |
| `content` | `string` | متن ساده پاسخ |
| `sections` | `ChatSection[]` | خروجی ساخت‌یافته برای رندر کارت‌ها |

#### ساختار `ChatSection`

| فیلد | نوع | اجباری | توضیح |
|------|-----|--------|-------|
| `type` | `'text' \| 'list' \| 'recommendation' \| 'warning'` | بله | نوع سکشن |
| `title` | `string` | خیر | عنوان سکشن |
| `content` | `string` | خیر | متن سکشن |
| `items` | `string[]` | خیر | برای لیست |
| `icon` | `'droplet' \| 'leaf' \| 'warning' \| 'fertilizer' \| 'calendar'` | خیر | آیکون نمایشی |
| `frequency` | `string` | خیر | فقط برای `recommendation` |
| `amount` | `string` | خیر | فقط برای `recommendation` |
| `timing` | `string` | خیر | فقط برای `recommendation` |
| `expandableExplanation` | `string` | خیر | توضیح بازشونده |

#### حداقل توصیه

- `sections` همیشه به صورت آرایه برگردد، حتی اگر خالی باشد.
- `conversation_id` بعد از اولین پاسخ حتماً برگردد.
- اگر پاسخ فقط structured است، `content` می‌تواند رشته خالی باشد.

---

## 2) Fertilization Recommendation

### صفحه

- `src/app/(dashboard)/(private)/fertilization-recommendation/page.tsx`
- کامپوننت اصلی: `src/views/dashboards/farm/smartFertilization/SmartFertilizationRecommendation.tsx`

### APIهای موردنیاز

1. `GET /api/fertilization-recommendation/config/`
2. `POST /api/fertilization-recommendation/recommend/`

---

### 2.1) دریافت config اولیه

#### Endpoint

`GET /api/fertilization-recommendation/config/`

#### Response

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
      { "id": "prePlanting", "icon": "tabler-seedling" },
      { "id": "earlyGrowth", "icon": "tabler-leaf" },
      { "id": "flowering", "icon": "tabler-flower" },
      { "id": "fruiting", "icon": "tabler-apple" },
      { "id": "postHarvest", "icon": "tabler-basket" }
    ],
    "cropOptions": [
      { "id": "wheat", "labelKey": "wheat", "icon": "tabler-wheat" },
      { "id": "corn", "labelKey": "corn", "icon": "tabler-plant-2" }
    ]
  }
}
```

#### فیلدهای لازم

##### `farmData`

| فیلد | نوع |
|------|-----|
| `soilType` | `string` |
| `organicMatter` | `string` |
| `waterEC` | `string` |

##### `growthStages[]`

| فیلد | نوع | توضیح |
|------|-----|-------|
| `id` | `string` | id مرحله رشد |
| `icon` | `string` | نام آیکون |

##### `cropOptions[]`

| فیلد | نوع | توضیح |
|------|-----|-------|
| `id` | `string` | id محصول برای submit |
| `labelKey` | `string` | کلید ترجمه |
| `icon` | `string` | نام آیکون |

#### نکته

- اگر `growthStages` مقدار داشته باشد، اولین آیتم به عنوان پیش‌فرض انتخاب می‌شود.
- اگر `cropOptions` خالی باشد، لیست انتخاب محصول خالی نمایش داده می‌شود.

---

### 2.2) دریافت برنامه کوددهی

#### Endpoint

`POST /api/fertilization-recommendation/recommend/`

#### Request body

```json
{
  "crop_id": "wheat",
  "growth_stage": "flowering",
  "soilType": "Loamy",
  "organicMatter": "Medium (2.5%)",
  "waterEC": "1.2 dS/m"
}
```

#### Response

```json
{
  "status": "success",
  "data": {
    "plan": {
      "npkRatio": "20-20-20",
      "amountPerHectare": "150 kg/ha",
      "applicationMethod": "Fertigation",
      "applicationInterval": "Every 10 days",
      "reasoning": "Balanced NPK is recommended during flowering to support bloom and fruit set."
    }
  }
}
```

#### فیلدهای لازم در `plan`

| فیلد | نوع | مصرف در UI |
|------|-----|------------|
| `npkRatio` | `string` | نوع/نسبت کود |
| `amountPerHectare` | `string` | مقدار مصرف |
| `applicationMethod` | `string` | روش مصرف |
| `applicationInterval` | `string` | بازه تکرار |
| `reasoning` | `string` | توضیح بازشونده |

#### نکته

فرانت مستقیماً `data.plan` را انتظار دارد. اگر `plan` نباشد، نتیجه‌ای نمایش داده نمی‌شود.

---

## 3) Irrigation Recommendation

### صفحه

- `src/app/(dashboard)/(private)/irrigation-recommendation/page.tsx`
- کامپوننت اصلی: `src/views/dashboards/farm/smartIrrigation/SmartIrrigationRecommendation.tsx`

### APIهای موردنیاز

1. `GET /api/irrigation-recommendation/config/`
2. `POST /api/irrigation-recommendation/recommend/`

---

### 3.1) دریافت config اولیه

#### Endpoint

`GET /api/irrigation-recommendation/config/`

#### Response

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
      { "id": "tomato", "labelKey": "tomato", "icon": "tabler-plant-2" },
      { "id": "cucumber", "labelKey": "cucumber", "icon": "tabler-leaf" }
    ]
  }
}
```

#### فیلدهای لازم

##### `farmInfo`

| فیلد | نوع |
|------|-----|
| `soilType` | `string` |
| `waterQuality` | `string` |
| `climateZone` | `string` |

##### `cropOptions[]`

| فیلد | نوع | توضیح |
|------|-----|-------|
| `id` | `string` | id محصول برای submit |
| `labelKey` | `string` | کلید ترجمه |
| `icon` | `string` | نام آیکون |

#### نکته

در این صفحه `farmInfo` بدون چک null مستقیماً set می‌شود؛ بهتر است API همیشه این آبجکت را برگرداند.

---

### 3.2) دریافت برنامه آبیاری

#### Endpoint

`POST /api/irrigation-recommendation/recommend/`

#### Request body

```json
{
  "crop_id": "tomato"
}
```

> در سرویس، فیلدهای `soilType`, `waterQuality`, `climateZone` هم پشتیبانی شده‌اند، ولی در UI فعلی فقط `crop_id` ارسال می‌شود.

#### Response

```json
{
  "status": "success",
  "data": {
    "plan": {
      "frequencyPerWeek": 3,
      "durationMinutes": 25,
      "bestTimeOfDay": "Early morning",
      "moistureLevel": 68,
      "warning": "Reduce irrigation if rainfall occurs this week."
    }
  }
}
```

#### فیلدهای لازم در `plan`

| فیلد | نوع | مصرف در UI |
|------|-----|------------|
| `frequencyPerWeek` | `number` | تعداد دفعات در هفته |
| `durationMinutes` | `number` | مدت هر نوبت |
| `bestTimeOfDay` | `string` | زمان مناسب آبیاری |
| `moistureLevel` | `number` | درصد moisture برای دایره progress |
| `warning` | `string` | هشدار اختیاری |

#### محدودیت مهم

- `moistureLevel` بهتر است بین `0` تا `100` باشد، چون مستقیم برای محاسبه progress circle استفاده می‌شود.

---

## جمع‌بندی سریع برای بک‌اند

### Farm AI Assistant

- `GET /api/farm-ai-assistant/context/` → `data: FarmContext`
- `POST /api/farm-ai-assistant/chat/` → `data: { message_id, conversation_id, content, sections }`

### Fertilization Recommendation

- `GET /api/fertilization-recommendation/config/` → `data: { farmData, growthStages, cropOptions }`
- `POST /api/fertilization-recommendation/recommend/` → `data: { plan }`

### Irrigation Recommendation

- `GET /api/irrigation-recommendation/config/` → `data: { farmInfo, cropOptions }`
- `POST /api/irrigation-recommendation/recommend/` → `data: { plan }`

---

## مسیرهای مرجع کد

- `src/libs/api/services/farmAiAssistantService.ts`
- `src/libs/api/services/fertilizationRecommendationService.ts`
- `src/libs/api/services/irrigationRecommendationService.ts`
- `src/views/dashboards/farm/farmAiAssistant/FarmAiAssistantChat.tsx`
- `src/views/dashboards/farm/smartFertilization/SmartFertilizationRecommendation.tsx`
- `src/views/dashboards/farm/smartIrrigation/SmartIrrigationRecommendation.tsx`
