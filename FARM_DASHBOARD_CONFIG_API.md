# مستند ارتباط فرانت با API تنظیمات داشبورد فارم

این فایل مشخص می‌کند فرانت‌اند برای endpoint زیر چه request و responseی انتظار دارد:

```text
http://localhost:8000/api/farm-dashboard-config
```

این endpoint در فرانت از طریق فایل `src/libs/api/services/farmDashboardService.ts` مصرف می‌شود.

---

## خلاصه رفتار فرانت

- فرانت برای دریافت تنظیمات از `GET /api/farm-dashboard-config` استفاده می‌کند.
- فرانت برای ذخیره تغییرات از `PATCH /api/farm-dashboard-config` استفاده می‌کند.
- در `PATCH` فقط فیلدهای تغییرکرده ارسال می‌شوند.
- اما در response بهتر است همیشه **کل تنظیمات نهایی** برگردانده شود.
- فرانت response را هم در حالت wrapper شده و هم بدون wrapper می‌پذیرد.

---

## فرمت response قابل قبول

فرانت هر دو فرمت زیر را می‌پذیرد.

### فرمت پیشنهادی

```json
{
  "code": 200,
  "msg": "OK",
  "data": {
    "disabled_card_ids": ["farmWeatherCard", "sensorRadarChart"],
    "row_order": [
      "overviewKpis",
      "weatherAlerts",
      "sensorMonitoring",
      "sensorCharts",
      "alertsWater",
      "predictions",
      "soilHeatmap",
      "ndviRecommendations",
      "economic"
    ],
    "enable_drag_reorder": true
  }
}
```

### فرمت قابل قبول بدون wrapper

```json
{
  "disabled_card_ids": ["farmWeatherCard", "sensorRadarChart"],
  "row_order": [
    "overviewKpis",
    "weatherAlerts",
    "sensorMonitoring",
    "sensorCharts",
    "alertsWater",
    "predictions",
    "soilHeatmap",
    "ndviRecommendations",
    "economic"
  ],
  "enable_drag_reorder": true
}
```

---

## GET

### Request

```http
GET /api/farm-dashboard-config
Content-Type: application/json
Authorization: Bearer <token>
```

> هدر `Authorization` فقط وقتی ارسال می‌شود که توکن در `localStorage` موجود باشد.

### Response مورد انتظار

فرانت در خروجی GET این ساختار را انتظار دارد:

| فیلد | نوع | توضیح |
|---|---|---|
| `disabled_card_ids` | `string[]` | لیست کارت‌های مخفی‌شده |
| `row_order` | `string[]` | ترتیب ردیف‌های داشبورد |
| `enable_drag_reorder` | `boolean` | فعال/غیرفعال بودن drag reorder |

### مثال response

```json
{
  "code": 200,
  "msg": "OK",
  "data": {
    "disabled_card_ids": ["farmWeatherCard", "sensorRadarChart"],
    "row_order": [
      "overviewKpis",
      "weatherAlerts",
      "sensorMonitoring",
      "sensorCharts",
      "alertsWater",
      "predictions",
      "soilHeatmap",
      "ndviRecommendations",
      "economic"
    ],
    "enable_drag_reorder": true
  }
}
```

### نکات مهم GET

- اگر `enable_drag_reorder` برنگردد، فرانت مقدار پیش‌فرض `true` در نظر می‌گیرد.
- اگر `row_order` نامعتبر یا خالی باشد، فرانت از ترتیب پیش‌فرض خودش استفاده می‌کند.
- اگر request خطا بخورد، فرانت اول `localStorage` را چک می‌کند؛ اگر چیزی نبود، config پیش‌فرض را می‌سازد.

---

## PATCH

### رفتار request

فرانت فقط فیلدهای تغییرکرده را می‌فرستد. یعنی body می‌تواند یکی از حالت‌های زیر باشد یا ترکیبی از آن‌ها:

#### 1) تغییر کارت‌های غیرفعال

```json
{
  "disabled_card_ids": ["farmWeatherCard", "sensorRadarChart"]
}
```

#### 2) تغییر ترتیب ردیف‌ها

```json
{
  "row_order": [
    "overviewKpis",
    "weatherAlerts",
    "predictions",
    "sensorMonitoring",
    "sensorCharts",
    "alertsWater",
    "soilHeatmap",
    "ndviRecommendations",
    "economic"
  ]
}
```

#### 3) فعال/غیرفعال کردن drag reorder

```json
{
  "enable_drag_reorder": false
}
```

#### 4) ترکیبی

```json
{
  "disabled_card_ids": ["farmWeatherCard"],
  "row_order": [
    "overviewKpis",
    "weatherAlerts",
    "sensorMonitoring",
    "sensorCharts",
    "alertsWater",
    "predictions",
    "soilHeatmap",
    "ndviRecommendations",
    "economic"
  ],
  "enable_drag_reorder": true
}
```

### Response مورد انتظار برای PATCH

هرچند request می‌تواند partial باشد، ولی response بهتر است همیشه **کل state نهایی config** را برگرداند:

```json
{
  "code": 200,
  "msg": "OK",
  "data": {
    "disabled_card_ids": ["farmWeatherCard"],
    "row_order": [
      "overviewKpis",
      "weatherAlerts",
      "sensorMonitoring",
      "sensorCharts",
      "alertsWater",
      "predictions",
      "soilHeatmap",
      "ndviRecommendations",
      "economic"
    ],
    "enable_drag_reorder": true
  }
}
```

### نکته خیلی مهم برای PATCH

در پیاده‌سازی فعلی فرانت، response باید حداقل یکی از این دو فیلد را داشته باشد:

- `disabled_card_ids`
- `row_order`

اگر backend فقط این را برگرداند:

```json
{
  "enable_drag_reorder": false
}
```

ممکن است فرانت این response را نامعتبر تشخیص دهد.  
بنابراین برای جلوگیری از مشکل، **همیشه کل object نهایی config را برگردانید**.

---

## mapping بین فرانت و API

فرانت state داخلی را با نام‌های camelCase نگه می‌دارد، اما در request به snake_case تبدیل می‌کند:

| Frontend field | API field |
|---|---|
| `disabledCardIds` | `disabled_card_ids` |
| `rowOrder` | `row_order` |
| `enableDragReorder` | `enable_drag_reorder` |

---

## مقادیر معتبر پیشنهادی

### Row ID های معتبر

```json
[
  "overviewKpis",
  "weatherAlerts",
  "sensorMonitoring",
  "sensorCharts",
  "alertsWater",
  "predictions",
  "soilHeatmap",
  "ndviRecommendations",
  "economic"
]
```

### Card ID های معتبر

```json
[
  "farmOverviewKpis",
  "farmWeatherCard",
  "farmAlertsTracker",
  "sensorValuesList",
  "sensorRadarChart",
  "sensorComparisonChart",
  "anomalyDetectionCard",
  "farmAlertsTimeline",
  "waterNeedPrediction",
  "harvestPredictionCard",
  "yieldPredictionChart",
  "soilMoistureHeatmap",
  "ndviHealthCard",
  "recommendationsList",
  "economicOverview"
]
```

---

## فرمت canonical پیشنهادی برای backend

اگر بخواهی backend کاملاً سازگار و بدون ambiguity باشد، بهترین قرارداد این است:

- `disabled_card_ids` فقط شامل `Card ID` باشد
- `row_order` فقط شامل `Row ID` باشد
- response همیشه full object برگرداند
- status موفق `200` باشد
- `Content-Type` برابر `application/json` باشد

---

## نمونه نهایی پیشنهادی

### GET success

```json
{
  "code": 200,
  "msg": "OK",
  "data": {
    "disabled_card_ids": [],
    "row_order": [
      "overviewKpis",
      "weatherAlerts",
      "sensorMonitoring",
      "sensorCharts",
      "alertsWater",
      "predictions",
      "soilHeatmap",
      "ndviRecommendations",
      "economic"
    ],
    "enable_drag_reorder": true
  }
}
```

### PATCH success

```json
{
  "code": 200,
  "msg": "OK",
  "data": {
    "disabled_card_ids": ["farmWeatherCard"],
    "row_order": [
      "overviewKpis",
      "weatherAlerts",
      "sensorMonitoring",
      "sensorCharts",
      "alertsWater",
      "predictions",
      "soilHeatmap",
      "ndviRecommendations",
      "economic"
    ],
    "enable_drag_reorder": false
  }
}
```

---

## منبع این مستند

این مستند بر اساس رفتار واقعی فرانت در فایل‌های زیر نوشته شده است:

- `src/libs/api/services/farmDashboardService.ts`
- `src/views/dashboards/farm/farmDashboardConfig.ts`
- `src/views/dashboards/farm/FarmDashboardWrapper.tsx`
