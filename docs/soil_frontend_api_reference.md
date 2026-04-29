# Soil API Reference for Frontend

این فایل برای فرانت آماده شده تا ساختار پاسخ APIهای خاک را سریع و شفاف داشته باشید.

## Base Notes

- سه endpoint زیر `farm_uuid` را به صورت query param لازم دارند:
  - `GET /api/soil/anomalies/`
  - `GET /api/soil/moisture-heatmap/`
  - `GET /api/soil/summary/`
- endpoint `GET /api/soil/avg-moisture/` بدون `farm_uuid` هم جواب می‌دهد، ولی اگر `farm_uuid` ارسال شود داده بر اساس همان مزرعه محاسبه می‌شود.
- در سه endpoint اول و سوم، اگر `farm_uuid` ارسال نشود یا مزرعه پیدا نشود، پاسخ با ساختار `code/msg/data` برمی‌گردد.
- پاسخ موفق `avg-moisture` با کلید `status` برمی‌گردد، ولی سه endpoint دیگر با کلیدهای `code`, `msg`, `data` برمی‌گردند.

---

## 1) Average Soil Moisture

### Endpoint

```http
GET /api/soil/avg-moisture/?farm_uuid=<farm_uuid>
```

### Query Params

| name | type | required | description |
|---|---|---:|---|
| `farm_uuid` | `string (uuid)` | no | UUID مزرعه |

### Success Response

```json
{
  "status": "success",
  "data": {
    "id": "avg_soil_moisture",
    "title": "میانگین رطوبت خاک",
    "subtitle": "کل مزرعه",
    "stats": "65%",
    "avatarColor": "primary",
    "avatarIcon": "tabler-plant-2",
    "chipText": "بهینه",
    "chipColor": "success"
  }
}
```

### Response Fields

| field | type | description |
|---|---|---|
| `status` | `string` | در حالت موفق مقدار `success` |
| `data.id` | `string` | شناسه کارت |
| `data.title` | `string` | عنوان کارت |
| `data.subtitle` | `string` | زیرعنوان کارت |
| `data.stats` | `string` | مقدار اصلی به صورت درصد، مثل `48%` |
| `data.avatarColor` | `string` | رنگ آیکن/کارت |
| `data.avatarIcon` | `string` | نام آیکن |
| `data.chipText` | `string` | وضعیت متنی، مثل `بهینه`، `متوسط`، `کم` |
| `data.chipColor` | `string` | رنگ وضعیت، مثل `success`، `warning`، `error` |

### Frontend Notes

- این endpoint برای ساخت یک KPI card مناسب است.
- `stats` همیشه string است و بهتر است مستقیم render شود.
- `chipText` و `chipColor` برای badge یا status pill استفاده شوند.

---

## 2) Soil Anomalies

### Endpoint

```http
GET /api/soil/anomalies/?farm_uuid=<farm_uuid>
```

### Query Params

| name | type | required | description |
|---|---|---:|---|
| `farm_uuid` | `string (uuid)` | yes | UUID مزرعه |

### Success Response

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "farm_uuid": "11111111-1111-1111-1111-111111111111",
    "summary": "Risk of localized soil imbalance detected.",
    "explanation": "One or more soil indicators are outside the expected range.",
    "likely_cause": "Uneven irrigation or nutrient distribution.",
    "recommended_action": "Inspect the affected zone and verify irrigation schedule.",
    "monitoring_priority": "high",
    "confidence": 0.89,
    "generated_at": "2025-01-01T10:30:00Z",
    "anomalies": [
      {
        "sensor": "رطوبت خاک زون 3",
        "value": "38%",
        "expected": "45-65%",
        "deviation": "-12%",
        "severity": "warning"
      }
    ],
    "interpretation": {
      "risk_level": "medium"
    },
    "knowledge_base": null,
    "raw_response": null
  }
}
```

### Response Fields

| field | type | description |
|---|---|---|
| `code` | `number` | در حالت موفق مقدار `200` |
| `msg` | `string` | در حالت موفق مقدار `success` |
| `data.farm_uuid` | `string` | UUID مزرعه |
| `data.summary` | `string` | خلاصه کوتاه نتیجه anomaly detection |
| `data.explanation` | `string` | توضیح readable برای فرانت |
| `data.likely_cause` | `string` | علت احتمالی |
| `data.recommended_action` | `string` | اقدام پیشنهادی |
| `data.monitoring_priority` | `string` | سطح اهمیت پایش؛ مثل `low`, `medium`, `high`, `urgent` |
| `data.confidence` | `number` | میزان اطمینان مدل |
| `data.generated_at` | `string` | زمان تولید تحلیل |
| `data.anomalies` | `array` | لیست anomalyها |
| `data.anomalies[].sensor` | `string` | نام سنسور یا ناحیه |
| `data.anomalies[].value` | `string` | مقدار فعلی |
| `data.anomalies[].expected` | `string` | بازه یا مقدار مورد انتظار |
| `data.anomalies[].deviation` | `string` | اختلاف با مقدار نرمال |
| `data.anomalies[].severity` | `string` | شدت anomaly، مثل `warning` یا `error` |
| `data.interpretation` | `object` | تفسیر ساختاریافته برای UI پیشرفته |
| `data.knowledge_base` | `string \| null` | مرجع دانشی در صورت وجود |
| `data.raw_response` | `string \| null` | متن خام upstream در صورت وجود |

### Error Response - Missing `farm_uuid`

```json
{
  "code": 400,
  "msg": "error",
  "data": {
    "farm_uuid": ["This field is required."]
  }
}
```

### Error Response - Farm Not Found

```json
{
  "code": 404,
  "msg": "error",
  "data": {
    "farm_uuid": ["Farm not found."]
  }
}
```

### Frontend Notes

- `anomalies` می‌تواند برای table، list یا alert cards استفاده شود.
- اگر `anomalies` خالی بود، UI بهتر است empty state نمایش دهد.
- `severity` را می‌توانید به color map وصل کنید.

---

## 3) Soil Moisture Heatmap

### Endpoint

```http
GET /api/soil/moisture-heatmap/?farm_uuid=<farm_uuid>
```

### Query Params

| name | type | required | description |
|---|---|---:|---|
| `farm_uuid` | `string (uuid)` | yes | UUID مزرعه |

### Success Response

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "farm_uuid": "11111111-1111-1111-1111-111111111111",
    "location": {
      "name": "Zone A"
    },
    "current_sensor": {
      "name": "Sensor 7-in-1"
    },
    "soil_profile": [],
    "timestamp": "2025-01-01T10:30:00Z",
    "grid_resolution": {
      "rows": 10,
      "cols": 10
    },
    "grid_cells": [],
    "sensor_points": [],
    "quality_legend": {
      "low": "0-30",
      "medium": "31-60",
      "high": "61-100"
    },
    "depth_layers": [],
    "model_metadata": {},
    "summary": {}
  }
}
```

### Supported Response Shape in Current Backend

در serializer فعلی این فیلدها پشتیبانی می‌شوند:

| field | type | description |
|---|---|---|
| `data.farm_uuid` | `string` | UUID مزرعه |
| `data.location` | `object` | اطلاعات مکانی |
| `data.current_sensor` | `object` | اطلاعات سنسور فعال |
| `data.soil_profile` | `array<object>` | داده لایه‌های خاک |
| `data.timestamp` | `string \| null` | زمان تولید heatmap |
| `data.grid_resolution` | `object` | رزولوشن grid |
| `data.grid_cells` | `array<object>` | سلول‌های grid |
| `data.sensor_points` | `array<object>` | نقاط سنسور |
| `data.quality_legend` | `object` | legend مقادیر |
| `data.depth_layers` | `array<object>` | لایه‌های عمقی |
| `data.model_metadata` | `object` | متادیتای مدل |
| `data.summary` | `object` | خلاصه تفسیری |

### Legacy / Mock Shape You May Also See

در داده mock داخلی پروژه یک ساختار ساده‌تر هم وجود دارد:

```json
{
  "status": "success",
  "data": {
    "zones": ["زون 1", "زون 2"],
    "hours": ["6 ص", "8 ص"],
    "series": [
      {
        "name": "زون 1",
        "data": [
          { "x": "6 ص", "y": 52 },
          { "x": "8 ص", "y": 48 }
        ]
      }
    ]
  }
}
```

### Error Response - Missing `farm_uuid`

```json
{
  "code": 400,
  "msg": "error",
  "data": {
    "farm_uuid": ["This field is required."]
  }
}
```

### Error Response - Farm Not Found

```json
{
  "code": 404,
  "msg": "error",
  "data": {
    "farm_uuid": ["Farm not found."]
  }
}
```

### Frontend Notes

- چون upstream shape ممکن است object-based یا series-based باشد، فرانت بهتر است defensive parsing داشته باشد.
- اگر `grid_cells` وجود داشت، heatmap را از grid render کنید.
- اگر `series` وجود داشت، می‌توانید آن را به chart heatmap یا matrix chart بدهید.

---

## 4) Soil Summary

### Endpoint

```http
GET /api/soil/summary/?farm_uuid=<farm_uuid>
```

### Query Params

| name | type | required | description |
|---|---|---:|---|
| `farm_uuid` | `string (uuid)` | yes | UUID مزرعه |

### Success Response

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "farm_uuid": "11111111-1111-1111-1111-111111111111",
    "healthScore": 82,
    "profileSource": "Tomato",
    "healthScoreDetails": {},
    "healthLanguage": {},
    "avgSoilMoisture": 46,
    "avgSoilMoistureRaw": 46.0,
    "avgSoilMoistureStatus": "بهینه"
  }
}
```

### Response Fields

| field | type | description |
|---|---|---|
| `code` | `number` | در حالت موفق مقدار `200` |
| `msg` | `string` | در حالت موفق مقدار `success` |
| `data.farm_uuid` | `string` | UUID مزرعه |
| `data.healthScore` | `number` | امتیاز سلامت کلی خاک |
| `data.profileSource` | `string` | منبع پروفایل یا محصول مرجع |
| `data.healthScoreDetails` | `object` | جزئیات محاسبه health score |
| `data.healthLanguage` | `object` | متن‌ها و labelهای قابل نمایش |
| `data.avgSoilMoisture` | `number` | میانگین گرد شده رطوبت خاک |
| `data.avgSoilMoistureRaw` | `number` | میانگین خام |
| `data.avgSoilMoistureStatus` | `string` | وضعیت متنی رطوبت خاک |

### Error Response - Missing `farm_uuid`

```json
{
  "code": 400,
  "msg": "error",
  "data": {
    "farm_uuid": ["This field is required."]
  }
}
```

### Error Response - Farm Not Found

```json
{
  "code": 404,
  "msg": "error",
  "data": {
    "farm_uuid": ["Farm not found."]
  }
}
```

### Frontend Notes

- این endpoint برای summary card یا hero panel خیلی مناسب است.
- `healthScoreDetails` و `healthLanguage` را optional در نظر بگیرید.
- برای UI بهتر، `healthScore` را هم به صورت عدد و هم به صورت progress/gauge نمایش دهید.

---

## Suggested Frontend Handling

- برای `avg-moisture` انتظار `status/data` داشته باشید.
- برای `anomalies`, `moisture-heatmap`, `summary` انتظار `code/msg/data` داشته باشید.
- برای خطاهای 400 و 404، متن خطا را از `data.farm_uuid[0]` بخوانید.
- در heatmap، parsing را flexible بنویسید چون shape داده ممکن است بسته به upstream تغییر کند.
