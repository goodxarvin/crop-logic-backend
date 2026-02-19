# مستندات API داشبورد Farm (Farm Dashboard)

این سند شامل توضیحات کل داشبورد، APIهای تنظیمات (disable/enable/move کارت‌ها) و ساختار پیشنهادی ریسپانس برای محتوای کارت‌ها است.

---

## ۱. نمای کلی داشبورد

داشبورد Farm از کامپوننت `FarmDashboardWrapper` استفاده می‌کند و شامل ردیف‌ها (rows) و کارت‌های (cards) زیر است:

| Row ID | Row Label | کارت‌ها |
|--------|-----------|---------|
| `overviewKpis` | Overview KPIs | `farmOverviewKpis` |
| `weatherAlerts` | Weather & Alerts | `farmWeatherCard`, `farmAlertsTracker` |
| `sensorMonitoring` | Sensor Monitoring | `sensorValuesList`, `sensorRadarChart` |
| `sensorCharts` | Sensor Charts | `sensorComparisonChart`, `anomalyDetectionCard` |
| `alertsWater` | Alerts & Water Prediction | `farmAlertsTimeline`, `waterNeedPrediction` |
| `predictions` | Predictions | `harvestPredictionCard`, `yieldPredictionChart` |
| `soilHeatmap` | Soil Moisture Heatmap | `soilMoistureHeatmap` |
| `ndviRecommendations` | NDVI & Recommendations | `ndviHealthCard`, `recommendationsList` |
| `economic` | Economic Overview | `economicOverview` |

---

## ۲. APIهای تنظیمات داشبورد

### ۲.۱ دریافت تنظیمات داشبورد (Get Config)

```
GET /api/farm-dashboard-config
```

**توضیح:** تنظیمات شخصی‌سازی داشبورد کاربر لاگین‌شده را برمی‌گرداند.

**Response:**
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

**فیلدها:**
| فیلد | نوع | توضیح |
|------|-----|-------|
| `disabled_card_ids` | `string[]` | لیست شناسه کارت‌های غیرفعال (hidden) |
| `row_order` | `string[]` | ترتیب نمایش ردیف‌ها |
| `enable_drag_reorder` | `boolean` | امکان جابجایی ردیف‌ها با drag |

---

### ۲.۲ غیرفعال کردن کارت (Disable Card)

```
PATCH /api/farm-dashboard-config
```

**Request Body:**
```json
{
  "disabled_card_ids": ["farmWeatherCard", "sensorRadarChart"]
}
```

کارت با شناسه `cardId` به لیست `disabled_card_ids` اضافه می‌شود و در داشبورد نمایش داده نمی‌شود.

---

### ۲.۳ فعال کردن کارت (Enable Card)

```
PATCH /api/farm-dashboard-config
```

**Request Body:**
```json
{
  "disabled_card_ids": ["farmWeatherCard"]
}
```

شناسه کارت از لیست `disabled_card_ids` حذف می‌شود و کارت دوباره نمایش داده می‌شود.

**نکته:** کل لیست `disabled_card_ids` جدید ارسال می‌شود؛ برای enable باید آرایه بدون آن کارت فرستاده شود.

---

### ۲.۴ جابجایی ردیف‌ها (Move Rows)

```
PATCH /api/farm-dashboard-config
```

**Request Body:**
```json
{
  "row_order": [
    "overviewKpis",
    "weatherAlerts",
    "sensorMonitoring",
    "predictions",
    "sensorCharts",
    "alertsWater",
    "soilHeatmap",
    "ndviRecommendations",
    "economic"
  ]
}
```

ترتیب ردیف‌ها طبق آرایه `row_order` ذخیره می‌شود.

---

### ۲.۵ تغییر وضعیت Drag Reorder

```
PATCH /api/farm-dashboard-config
```

**Request Body:**
```json
{
  "enable_drag_reorder": false
}
```

---

## ۳. API دریافت همه دیتای کارت‌ها

### Endpoint پیشنهادی

```
GET /api/farm-dashboard
```

یا به تفکیک کارت:
```
GET /api/farm-dashboard/cards
```

---

## ۴. لیست کامل ریسپانس هر کارت

ساختار پیشنهادی response برای محتوای هر کارت (بر اساس داده‌های mock فعلی در فرانت):

### ۴.۱ farmOverviewKpis

```json
{
  "kpis": [
    {
      "id": "farm_health_score",
      "title": "Farm Health Score",
      "subtitle": "AI Analysis",
      "stats": "87%",
      "avatarColor": "success",
      "avatarIcon": "tabler-heartbeat",
      "chipText": "Good",
      "chipColor": "success"
    },
    {
      "id": "water_stress_index",
      "title": "Water Stress Index",
      "subtitle": "Current",
      "stats": "12%",
      "avatarColor": "info",
      "avatarIcon": "tabler-droplet",
      "chipText": "Low",
      "chipColor": "success"
    },
    {
      "id": "disease_risk",
      "title": "Disease Risk",
      "subtitle": "Last 7 Days",
      "stats": "Low",
      "avatarColor": "success",
      "avatarIcon": "tabler-bug",
      "chipText": "5%",
      "chipColor": "success"
    },
    {
      "id": "avg_soil_moisture",
      "title": "Avg Soil Moisture",
      "subtitle": "Field-wide",
      "stats": "65%",
      "avatarColor": "primary",
      "avatarIcon": "tabler-plant-2",
      "chipText": "Optimal",
      "chipColor": "success"
    },
    {
      "id": "yield_prediction",
      "title": "Yield Prediction",
      "subtitle": "This Season",
      "stats": "42 ton",
      "avatarColor": "secondary",
      "avatarIcon": "tabler-chart-bar",
      "chipText": "+8%",
      "chipColor": "success"
    },
    {
      "id": "pest_risk",
      "title": "Pest Risk",
      "subtitle": "AI Forecast",
      "stats": "15%",
      "avatarColor": "warning",
      "avatarIcon": "tabler-bug-off",
      "chipText": "Monitor",
      "chipColor": "warning"
    }
  ]
}
```

---

### ۴.۲ farmWeatherCard

```json
{
  "condition": "Clear",
  "temperature": 24,
  "unit": "°C",
  "humidity": 45,
  "windSpeed": 12,
  "windUnit": "km/h",
  "chartData": {
    "labels": ["6am", "9am", "12pm", "3pm", "6pm", "9pm", "12am"],
    "series": [[18, 22, 26, 28, 25, 20, 18]]
  }
}
```

---

### ۴.۳ farmAlertsTracker

```json
{
  "totalAlerts": 3,
  "radialBarValue": 30,
  "alertStats": [
    {
      "title": "Water Shortage",
      "count": "2",
      "avatarColor": "error",
      "avatarIcon": "tabler-droplet-half-2"
    },
    {
      "title": "Fungal Risk",
      "count": "1",
      "avatarColor": "warning",
      "avatarIcon": "tabler-mushroom"
    },
    {
      "title": "Frost Alert",
      "count": "0",
      "avatarColor": "info",
      "avatarIcon": "tabler-snowflake"
    }
  ]
}
```

---

### ۴.۴ sensorValuesList

```json
{
  "sensors": [
    {
      "title": "28°C",
      "subtitle": "Air Temperature",
      "trendNumber": 2.1,
      "trend": "positive",
      "unit": "°C"
    },
    {
      "title": "24°C",
      "subtitle": "Soil Temperature",
      "trendNumber": -0.5,
      "trend": "negative",
      "unit": "°C"
    },
    {
      "title": "65%",
      "subtitle": "Air Humidity",
      "trendNumber": 3.2,
      "trend": "positive",
      "unit": "%"
    },
    {
      "title": "42%",
      "subtitle": "Soil Moisture (10cm)",
      "trendNumber": -1.8,
      "trend": "negative",
      "unit": "%"
    },
    {
      "title": "6.8",
      "subtitle": "Soil pH",
      "trendNumber": 0.2,
      "trend": "positive",
      "unit": "pH"
    },
    {
      "title": "1.2",
      "subtitle": "EC (dS/m)",
      "trendNumber": 0.1,
      "trend": "positive",
      "unit": "dS/m"
    },
    {
      "title": "850",
      "subtitle": "Light Intensity (lux)",
      "trendNumber": 15.3,
      "trend": "positive",
      "unit": "lux"
    },
    {
      "title": "12",
      "subtitle": "Wind Speed (km/h)",
      "trendNumber": -2.4,
      "trend": "negative",
      "unit": "km/h"
    }
  ]
}
```

---

### ۴.۵ sensorRadarChart

```json
{
  "labels": ["Temp", "Humidity", "pH", "EC", "Light", "Wind"],
  "series": [
    { "name": "Today", "data": [75, 65, 80, 70, 85, 60] },
    { "name": "Ideal", "data": [80, 70, 75, 75, 90, 50] }
  ]
}
```

---

### ۴.۶ sensorComparisonChart

```json
{
  "currentValue": 48,
  "vsLastWeek": "+5%",
  "vsLastWeekValue": 5,
  "categories": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
  "series": [
    { "name": "Today", "data": [42, 45, 48, 52, 50, 48, 46] },
    { "name": "Last Week", "data": [38, 40, 42, 45, 43, 40, 38] }
  ]
}
```

---

### ۴.۷ anomalyDetectionCard

```json
{
  "anomalies": [
    {
      "sensor": "Soil Moisture Z3",
      "value": "38%",
      "expected": "45-65%",
      "deviation": "-12%",
      "severity": "warning"
    },
    {
      "sensor": "pH Sector 2",
      "value": "5.2",
      "expected": "6.0-7.0",
      "deviation": "-0.8",
      "severity": "error"
    }
  ]
}
```

---

### ۴.۸ farmAlertsTimeline

```json
{
  "alerts": [
    {
      "title": "Water Shortage Risk",
      "description": "Soil moisture at 10cm depth (42%) is below optimal. AI predicts stress in 2-3 days if no irrigation. Recommended: irrigate within 24h.",
      "time": "15 min ago",
      "color": "warning"
    },
    {
      "title": "Fungal Disease Risk",
      "description": "High humidity (65%) + temp 24°C creates favorable conditions for fungal growth. Consider preventive fungicide or reduce irrigation.",
      "time": "1 hour ago",
      "color": "error"
    },
    {
      "title": "Irrigation Suggestion",
      "description": "Optimal watering window: 6:00-8:00 AM. Suggested amount: 450 m³ for Zone A. Expected efficiency gain: 12%.",
      "time": "2 hours ago",
      "color": "info"
    },
    {
      "title": "Soil Salinity Check",
      "description": "EC reading 1.2 dS/m is within range. No action needed. Next check recommended in 5 days.",
      "time": "4 hours ago",
      "color": "success"
    }
  ]
}
```

---

### ۴.۹ waterNeedPrediction

```json
{
  "totalNext7Days": 3290,
  "unit": "m³",
  "categories": ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7"],
  "series": [{ "name": "Water Need", "data": [420, 450, 480, 460, 490, 510, 480] }]
}
```

---

### ۴.۱۰ harvestPredictionCard

```json
{
  "date": "2025-10-15",
  "dateFormatted": "Oct 15, 2025",
  "daysUntil": 58,
  "description": "Based on current GDD accumulation and weather forecast. Optimal harvest window: Oct 12-18.",
  "optimalWindowStart": "2025-10-12",
  "optimalWindowEnd": "2025-10-18"
}
```

---

### ۴.۱۱ yieldPredictionChart

```json
{
  "categories": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
  "series": [
    { "name": "This Year", "data": [35, 38, 40, 42, 45, 48, 50, 48, 46, 44, 42, 42] },
    { "name": "Last Year", "data": [32, 34, 36, 38, 40, 42, 44, 42, 40, 38, 36, 38] }
  ],
  "summary": [
    { "title": "Predicted Yield", "subtitle": "This Season", "amount": "42 ton", "avatarColor": "primary", "avatarIcon": "tabler-chart-bar" },
    { "title": "Harvest Date", "subtitle": "Est. Oct 15", "amount": "+8%", "avatarColor": "success", "avatarIcon": "tabler-calendar" }
  ]
}
```

---

### ۴.۱۲ soilMoistureHeatmap

```json
{
  "zones": ["Z1", "Z2", "Z3", "Z4", "Z5", "Z6", "Z7"],
  "hours": ["6h", "8h", "10h", "12h", "14h", "16h", "18h"],
  "series": [
    { "name": "Z1", "data": [{"x": "6h", "y": 52}, {"x": "8h", "y": 48}, {"x": "10h", "y": 55}, {"x": "12h", "y": 60}, {"x": "14h", "y": 58}, {"x": "16h", "y": 54}, {"x": "18h", "y": 50}] },
    { "name": "Z2", "data": [{"x": "6h", "y": 45}, {"x": "8h", "y": 42}, {"x": "10h", "y": 48}, {"x": "12h", "y": 52}, {"x": "14h", "y": 50}, {"x": "16h", "y": 47}, {"x": "18h", "y": 44}] }
  ]
}
```

---

### ۴.۱۳ ndviHealthCard

```json
{
  "ndviIndex": 0.78,
  "healthData": [
    { "title": "Nitrogen Stress", "value": "Low", "color": "success", "icon": "tabler-leaf" },
    { "title": "Crop Health", "value": "Good", "color": "success", "icon": "tabler-plant" }
  ]
}
```

---

### ۴.۱۴ recommendationsList

```json
{
  "recommendations": [
    {
      "title": "Irrigation: 6:00-8:00 AM",
      "subtitle": "450 m³ for Zone A. Without irrigation, yield may drop ~8%.",
      "avatarIcon": "tabler-droplet",
      "avatarColor": "primary"
    },
    {
      "title": "Fertilizer: NPK 20-20-20",
      "subtitle": "Apply 25 kg/ha in 7 days. Current N deficiency in sector 2.",
      "avatarIcon": "tabler-leaf",
      "avatarColor": "success"
    },
    {
      "title": "Fungicide: Preventive",
      "subtitle": "Humidity + temp favor fungi. Consider copper-based spray.",
      "avatarIcon": "tabler-mushroom",
      "avatarColor": "warning"
    },
    {
      "title": "Harvest Window: Oct 12-18",
      "subtitle": "Peak ripeness expected Oct 15. Plan labor accordingly.",
      "avatarIcon": "tabler-calendar-event",
      "avatarColor": "info"
    }
  ]
}
```

---

### ۴.۱۵ economicOverview

```json
{
  "economicData": [
    { "title": "Water Cost", "value": "€720", "subtitle": "This month", "avatarIcon": "tabler-droplet", "avatarColor": "primary" },
    { "title": "AI Water Savings", "value": "€156", "subtitle": "18% saved", "avatarIcon": "tabler-bulb", "avatarColor": "success" },
    { "title": "Platform ROI", "value": "127%", "subtitle": "vs last year", "avatarIcon": "tabler-chart-line", "avatarColor": "info" },
    { "title": "Income Forecast", "value": "€42k", "subtitle": "This season", "avatarIcon": "tabler-currency-euro", "avatarColor": "success" }
  ],
  "chartSeries": [
    { "name": "Water Cost", "data": [120, 115, 110, 125, 118, 122] },
    { "name": "Fertilizer", "data": [80, 85, 90, 75, 82, 78] }
  ],
  "chartCategories": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
}
```

---

## ۵. Response یکپارچه همه کارت‌ها

اگر یک endpoint برای کل دیتای داشبورد داشته باشید:

```
GET /api/farm-dashboard
```

**Response پیشنهادی:**
```json
{
  "code": 200,
  "msg": "OK",
  "data": {
    "farmOverviewKpis": { ... },
    "farmWeatherCard": { ... },
    "farmAlertsTracker": { ... },
    "sensorValuesList": { ... },
    "sensorRadarChart": { ... },
    "sensorComparisonChart": { ... },
    "anomalyDetectionCard": { ... },
    "farmAlertsTimeline": { ... },
    "waterNeedPrediction": { ... },
    "harvestPredictionCard": { ... },
    "yieldPredictionChart": { ... },
    "soilMoistureHeatmap": { ... },
    "ndviHealthCard": { ... },
    "recommendationsList": { ... },
    "economicOverview": { ... }
  }
}
```

---

## ۶. خلاصه Endpoints

| عملیات | Method | Endpoint | Body |
|--------|--------|----------|------|
| دریافت تنظیمات | GET | `/api/farm-dashboard-config` | - |
| غیرفعال کردن کارت | PATCH | `/api/farm-dashboard-config` | `{ "disabled_card_ids": [...] }` |
| فعال کردن کارت | PATCH | `/api/farm-dashboard-config` | `{ "disabled_card_ids": [...] }` |
| جابجایی ردیف‌ها | PATCH | `/api/farm-dashboard-config` | `{ "row_order": [...] }` |
| Enable/Disable Drag | PATCH | `/api/farm-dashboard-config` | `{ "enable_drag_reorder": boolean }` |
| دیتای همه کارت‌ها | GET | `/api/farm-dashboard` یا `/api/farm-dashboard/cards` | - |

---

## ۷. Card IDs معتبر

```
farmOverviewKpis
farmWeatherCard
farmAlertsTracker
sensorValuesList
sensorRadarChart
sensorComparisonChart
anomalyDetectionCard
farmAlertsTimeline
waterNeedPrediction
harvestPredictionCard
yieldPredictionChart
soilMoistureHeatmap
ndviHealthCard
recommendationsList
economicOverview
```

## ۸. Row IDs معتبر

```
overviewKpis
weatherAlerts
sensorMonitoring
sensorCharts
alertsWater
predictions
soilHeatmap
ndviRecommendations
economic
```
