# مستند فرانت API سنسورها

این فایل برای تیم فرانت نوشته شده و رفتار کامل endpointهای زیر را توضیح می‌دهد:

- `GET /api/sensor-7-in-1/summary/`
- `GET /api/sensors/comparison-chart/`
- `GET /api/sensors/radar-chart/`
- `GET /api/sensors/values-list/`
- `GET /api/sensor-external-api/logs/`

---

## 1) نکات کلی

### Base URL

همه مسیرها نسبت به دامنه اصلی backend تعریف می‌شوند. مثال:

```txt
https://example.com/api/sensor-7-in-1/summary/
```

### نوع احراز هویت

این endpointها دو مدل احراز هویت دارند:

1. endpointهای سنسور 7-in-1:
   - `GET /api/sensor-7-in-1/summary/`
   - `GET /api/sensors/comparison-chart/`
   - `GET /api/sensors/radar-chart/`
   - `GET /api/sensors/values-list/`
   - نیازمند کاربر لاگین‌شده هستند.
   - اگر کاربر احراز هویت نشده باشد معمولاً پاسخ `401 Unauthorized` برمی‌گردد.

2. endpoint لاگ سنسور خارجی:
   - `GET /api/sensor-external-api/logs/`
   - نیازمند هدر `X-API-Key` است.
   - اگر API key ارسال نشود یا اشتباه باشد پاسخ `401 Unauthorized` برمی‌گردد.

### نکته مهم درباره ساختار response

این 5 API یکدست نیستند:

- `summary` پاسخ را داخل ساختار استاندارد `code / msg / data` برمی‌گرداند.
- `comparison-chart`، `radar-chart` و `values-list` داده خام را مستقیم برمی‌گردانند.
- `sensor-external-api/logs` پاسخ را به‌صورت paginated و داخل `code / msg / data` برمی‌گرداند.

پس فرانت باید برای هر endpoint دقیقاً همان ساختار را هندل کند.

---

## 2) GET /api/sensor-7-in-1/summary/

### هدف

این endpoint یک summary کامل از سنسور 7-in-1 مزرعه برمی‌گرداند و چند ویجت آماده برای UI را یکجا در خروجی قرار می‌دهد:

- اطلاعات متای سنسور
- لیست مقادیر سنسور
- کارت میانگین رطوبت خاک
- نمودار رادار
- نمودار مقایسه‌ای
- کارت anomaly detection
- heatmap رطوبت خاک

### احراز هویت

- نیازمند احراز هویت کاربر

### Query Params

| نام | نوع | اجباری | توضیح |
|---|---|---:|---|
| `farm_uuid` | `uuid` | بله | شناسه مزرعه |

### نمونه درخواست

```http
GET /api/sensor-7-in-1/summary/?farm_uuid=11111111-1111-1111-1111-111111111111
Authorization: Bearer <access_token>
```

### ساختار پاسخ موفق

```json
{
  "code": 200,
  "msg": "OK",
  "data": {
    "sensor": {},
    "sensorValuesList": {},
    "avgSoilMoisture": {},
    "sensorRadarChart": {},
    "sensorComparisonChart": {},
    "anomalyDetectionCard": {},
    "soilMoistureHeatmap": {}
  }
}
```

### فیلدهای `data`

#### `sensor`

متادیتای سنسور اصلی:

| فیلد | نوع | توضیح |
|---|---|---|
| `name` | `string` | نام سنسور |
| `physicalDeviceUuid` | `string \| null` | شناسه فیزیکی دستگاه |
| `sensorCatalogCode` | `string` | کد سنسور در catalog |
| `updatedAt` | `string \| null` | زمان آخرین لاگ به فرمت ISO |

نمونه:

```json
{
  "name": "Soil Sensor 7-in-1",
  "physicalDeviceUuid": "33333333-3333-3333-3333-333333333333",
  "sensorCatalogCode": "sensor-7-in-1",
  "updatedAt": "2025-01-10T08:30:00Z"
}
```

#### `sensorValuesList`

لیست مقادیر فعلی سنسور برای نمایش کارت‌ها یا stat itemها:

| فیلد | نوع | توضیح |
|---|---|---|
| `sensor` | `object` | همان متادیتای سنسور |
| `sensors` | `array` | لیست سنسورفیلدها |

ساختار هر آیتم `sensors`:

| فیلد | نوع | توضیح |
|---|---|---|
| `id` | `string` | کلید داخلی فیلد مثل `soil_moisture` |
| `title` | `string` | مقدار فرمت‌شده برای نمایش |
| `subtitle` | `string` | عنوان فارسی فیلد |
| `trendNumber` | `number` | مقدار تغییر نسبت به لاگ قبلی |
| `trend` | `positive \| negative` | جهت تغییر |
| `unit` | `string` | واحد |

نمونه:

```json
{
  "sensor": {
    "name": "Soil Sensor 7-in-1",
    "physicalDeviceUuid": "33333333-3333-3333-3333-333333333333",
    "sensorCatalogCode": "sensor-7-in-1",
    "updatedAt": "2025-01-10T08:30:00Z"
  },
  "sensors": [
    {
      "id": "soil_moisture",
      "title": "48.5%",
      "subtitle": "رطوبت خاک",
      "trendNumber": 7.5,
      "trend": "positive",
      "unit": "%"
    },
    {
      "id": "soil_temperature",
      "title": "23.2°C",
      "subtitle": "دمای خاک",
      "trendNumber": 2.2,
      "trend": "positive",
      "unit": "°C"
    }
  ]
}
```

#### `avgSoilMoisture`

کارت KPI برای میانگین رطوبت خاک:

| فیلد | نوع | توضیح |
|---|---|---|
| `id` | `string` | شناسه کارت |
| `title` | `string` | عنوان کارت |
| `subtitle` | `string` | زیرعنوان |
| `stats` | `string` | مقدار اصلی برای نمایش |
| `avatarColor` | `string` | رنگ آیکن/اواتار |
| `avatarIcon` | `string` | نام آیکن |
| `chipText` | `string` | متن وضعیت |
| `chipColor` | `string` | رنگ وضعیت |

نمونه:

```json
{
  "id": "avg_soil_moisture",
  "title": "میانگین رطوبت خاک",
  "subtitle": "سنسور 7 در 1 خاک",
  "stats": "48.5%",
  "avatarColor": "warning",
  "avatarIcon": "tabler-droplet",
  "chipText": "متوسط",
  "chipColor": "warning"
}
```

#### `sensorRadarChart`

داده آماده برای radar chart:

| فیلد | نوع | توضیح |
|---|---|---|
| `labels` | `string[]` | نام محورها |
| `series` | `array` | سری‌های نمودار |

ساختار هر `series`:

| فیلد | نوع |
|---|---|
| `name` | `string` |
| `data` | `number[]` |

نمونه:

```json
{
  "labels": ["رطوبت", "دما", "pH", "EC", "نیتروژن", "فسفر", "پتاسیم"],
  "series": [
    {
      "name": "اکنون",
      "data": [86.0, 96.0, 88.0, 84.0, 76.0, 88.0, 44.0]
    },
    {
      "name": "هدف",
      "data": [100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0]
    }
  ]
}
```

#### `sensorComparisonChart`

خروجی آماده برای line/area chart:

| فیلد | نوع | توضیح |
|---|---|---|
| `currentValue` | `number` | مقدار آخر |
| `vsLastWeek` | `string` | درصد تغییر نسبت به اولین نقطه |
| `vsLastWeekValue` | `number` | نسخه عددی تغییر |
| `categories` | `string[]` | برچسب محور X |
| `series` | `array` | سری‌های نمودار |

نمونه:

```json
{
  "currentValue": 48.5,
  "vsLastWeek": "+18.3%",
  "vsLastWeekValue": 18.3,
  "categories": ["01/04 08:00", "01/10 08:30"],
  "series": [
    {
      "name": "رطوبت خاک",
      "data": [41.0, 48.5]
    },
    {
      "name": "بازه هدف",
      "data": [55.0, 55.0]
    }
  ]
}
```

#### `anomalyDetectionCard`

لیست ناهنجاری‌های سنسور:

| فیلد | نوع | توضیح |
|---|---|---|
| `anomalies` | `array` | لیست anomaly |

ساختار هر anomaly:

| فیلد | نوع | توضیح |
|---|---|---|
| `sensor` | `string` | نام سنسور/پارامتر |
| `value` | `string` | مقدار فعلی |
| `expected` | `string` | بازه مورد انتظار |
| `deviation` | `string` | اختلاف با مقدار مورد انتظار |
| `severity` | `success \| warning \| error` | شدت |

نمونه:

```json
{
  "anomalies": [
    {
      "sensor": "پتاسیم",
      "value": "24 mg/kg",
      "expected": "15-35 mg/kg",
      "deviation": "0",
      "severity": "success"
    }
  ]
}
```

نکته:

- اگر ناهنجاری واقعی وجود نداشته باشد، backend یک آیتم success برمی‌گرداند تا UI حالت خالی نداشته باشد.

#### `soilMoistureHeatmap`

خروجی heatmap:

| فیلد | نوع | توضیح |
|---|---|---|
| `zones` | `string[]` | نام zoneها یا سنسورها |
| `hours` | `string[]` | محور زمان |
| `series` | `array` | داده heatmap |

نمونه:

```json
{
  "zones": ["Soil Sensor 7-in-1"],
  "hours": ["08:00", "10:00"],
  "series": [
    {
      "name": "Soil Sensor 7-in-1",
      "data": [
        { "x": "08:00", "y": 41.0 },
        { "x": "10:00", "y": 48.5 }
      ]
    }
  ]
}
```

### نمونه پاسخ کامل موفق

```json
{
  "code": 200,
  "msg": "OK",
  "data": {
    "sensor": {
      "name": "Soil Sensor 7-in-1",
      "physicalDeviceUuid": "33333333-3333-3333-3333-333333333333",
      "sensorCatalogCode": "sensor-7-in-1",
      "updatedAt": "2025-01-10T08:30:00Z"
    },
    "sensorValuesList": {
      "sensor": {
        "name": "Soil Sensor 7-in-1",
        "physicalDeviceUuid": "33333333-3333-3333-3333-333333333333",
        "sensorCatalogCode": "sensor-7-in-1",
        "updatedAt": "2025-01-10T08:30:00Z"
      },
      "sensors": [
        {
          "id": "soil_moisture",
          "title": "48.5%",
          "subtitle": "رطوبت خاک",
          "trendNumber": 7.5,
          "trend": "positive",
          "unit": "%"
        },
        {
          "id": "soil_temperature",
          "title": "23.2°C",
          "subtitle": "دمای خاک",
          "trendNumber": 2.2,
          "trend": "positive",
          "unit": "°C"
        },
        {
          "id": "soil_ph",
          "title": "6.8",
          "subtitle": "pH خاک",
          "trendNumber": 0.3,
          "trend": "positive",
          "unit": "pH"
        },
        {
          "id": "electrical_conductivity",
          "title": "1.4 dS/m",
          "subtitle": "هدایت الکتریکی",
          "trendNumber": 0.4,
          "trend": "positive",
          "unit": "dS/m"
        }
      ]
    },
    "avgSoilMoisture": {
      "id": "avg_soil_moisture",
      "title": "میانگین رطوبت خاک",
      "subtitle": "سنسور 7 در 1 خاک",
      "stats": "48.5%",
      "avatarColor": "warning",
      "avatarIcon": "tabler-droplet",
      "chipText": "متوسط",
      "chipColor": "warning"
    },
    "sensorRadarChart": {
      "labels": ["رطوبت", "دما", "pH", "EC", "نیتروژن", "فسفر", "پتاسیم"],
      "series": [
        {
          "name": "اکنون",
          "data": [86.0, 96.0, 88.0, 84.0, 76.0, 88.0, 44.0]
        },
        {
          "name": "هدف",
          "data": [100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0]
        }
      ]
    },
    "sensorComparisonChart": {
      "currentValue": 48.5,
      "vsLastWeek": "+18.3%",
      "vsLastWeekValue": 18.3,
      "categories": ["01/04 08:00", "01/10 08:30"],
      "series": [
        {
          "name": "رطوبت خاک",
          "data": [41.0, 48.5]
        },
        {
          "name": "بازه هدف",
          "data": [55.0, 55.0]
        }
      ]
    },
    "anomalyDetectionCard": {
      "anomalies": [
        {
          "sensor": "سنسور 7 در 1 خاک",
          "value": "نرمال",
          "expected": "تمام شاخص‌ها در بازه مجاز هستند",
          "deviation": "0",
          "severity": "success"
        }
      ]
    },
    "soilMoistureHeatmap": {
      "zones": ["Soil Sensor 7-in-1"],
      "hours": ["08:00", "10:00"],
      "series": [
        {
          "name": "Soil Sensor 7-in-1",
          "data": [
            { "x": "08:00", "y": 41.0 },
            { "x": "10:00", "y": 48.5 }
          ]
        }
      ]
    }
  }
}
```

### خطاهای ممکن

#### `400 Bad Request`

اگر `farm_uuid` ارسال نشود:

```json
{
  "farm_uuid": ["This field is required."]
}
```

اگر مزرعه برای این کاربر پیدا نشود:

```json
{
  "farm_uuid": ["Farm not found."]
}
```

اگر مزرعه سنسور نداشته باشد:

```json
{
  "farm_uuid": ["No sensor found for this farm."]
}
```

#### `401 Unauthorized`

اگر کاربر لاگین نباشد.

### نکات فرانت

- این endpoint برای ساخت dashboard کامل مناسب است.
- `updatedAt` ممکن است `null` باشد.
- اگر داده واقعی هنوز وارد نشده باشد backend ممکن است fallback/mock structure برگرداند.
- برای UI بهتر است روی وجود نداشتن بعضی فیلدها defensive code داشته باشید.

---

## 3) GET /api/sensors/comparison-chart/

### هدف

این endpoint داده خام نمودار مقایسه‌ای را برمی‌گرداند. خروجی آن برای chart component مناسب است و wrapper `code/msg/data` ندارد.

### احراز هویت

- نیازمند احراز هویت کاربر

### Query Params

| نام | نوع | اجباری | پیش‌فرض | توضیح |
|---|---|---:|---|---|
| `farm_uuid` | `uuid` | بله | - | شناسه مزرعه |
| `range` | `string` | خیر | `7d` | فقط `7d` یا `30d` |

### نمونه درخواست

```http
GET /api/sensors/comparison-chart/?farm_uuid=11111111-1111-1111-1111-111111111111&range=7d
Authorization: Bearer <access_token>
```

### پاسخ موفق

```json
{
  "series": [
    {
      "name": "moisture",
      "data": [41.0, 48.5]
    },
    {
      "name": "temperature",
      "data": [21.0, 23.2]
    },
    {
      "name": "ph",
      "data": [6.5, 6.8]
    }
  ],
  "categories": ["شنبه", "یکشنبه"],
  "currentValue": 48.5,
  "vsLastWeek": "+18.3%"
}
```

### توضیح فیلدها

| فیلد | نوع | توضیح |
|---|---|---|
| `series` | `array` | تمام پارامترهای عددی موجود در payload |
| `series[].name` | `string` | نام normalized فیلد مثل `moisture`، `temperature`، `ph` |
| `series[].data` | `number[]` | نقاط سری |
| `categories` | `string[]` | برچسب‌های محور X |
| `currentValue` | `number` | آخرین مقدار سری اول |
| `vsLastWeek` | `string` | درصد تغییر آخرین مقدار نسبت به اولین مقدار سری اول |

### رفتار `range`

- `7d`: دسته‌بندی روی روزهای هفته فارسی انجام می‌شود.
- `30d`: برچسب‌ها به‌صورت `MM/DD` برمی‌گردند.

### نکات مهم فرانت

- نام سری‌ها انگلیسی و normalized هستند، نه label نمایشی.
- `currentValue` و `vsLastWeek` همیشه از سری اول محاسبه می‌شوند.
- اگر هیچ داده‌ای وجود نداشته باشد پاسخ این شکلی است:

```json
{
  "series": [],
  "categories": [],
  "currentValue": 0.0,
  "vsLastWeek": "+0.0%"
}
```

### خطاهای ممکن

#### `400 Bad Request`

اگر `range` نامعتبر باشد:

```json
{
  "range": ["\"14d\" is not a valid choice."]
}
```

#### `401 Unauthorized`

اگر کاربر لاگین نباشد.

---

## 4) GET /api/sensors/radar-chart/

### هدف

این endpoint داده خام radar chart را برای سنسور مزرعه برمی‌گرداند.

### احراز هویت

- نیازمند احراز هویت کاربر

### Query Params

| نام | نوع | اجباری | پیش‌فرض | توضیح |
|---|---|---:|---|---|
| `farm_uuid` | `uuid` | بله | - | شناسه مزرعه |
| `range` | `string` | خیر | `7d` | فقط `today`، `7d` یا `30d` |

### نمونه درخواست

```http
GET /api/sensors/radar-chart/?farm_uuid=11111111-1111-1111-1111-111111111111&range=7d
Authorization: Bearer <access_token>
```

### پاسخ موفق

```json
{
  "labels": ["Moisture", "Temperature", "PH", "EC", "Nitrogen", "Potassium"],
  "series": [
    {
      "name": "وضعیت فعلی",
      "data": [48.5, 23.2, 6.8, 1.4, 31.0, 24.0]
    },
    {
      "name": "بازه ایده آل",
      "data": [60.0, 26.0, 6.5, 1.3, 42.0, 38.0]
    }
  ]
}
```

### توضیح فیلدها

| فیلد | نوع | توضیح |
|---|---|---|
| `labels` | `string[]` | محورهای radar chart |
| `series` | `array` | دو سری اصلی |
| `series[0]` | `object` | مقدار فعلی |
| `series[1]` | `object` | مقدار ایده‌آل |

### نکات مهم فرانت

- تعداد `labels` و طول `data` هر سری باید برابر باشد.
- فقط فیلدهایی در پاسخ می‌آیند که در آخرین payload وجود داشته باشند.
- اگر داده‌ای پیدا نشود:

```json
{
  "labels": [],
  "series": []
}
```

### خطاهای ممکن

#### `400 Bad Request`

اگر `range` نامعتبر باشد:

```json
{
  "range": ["\"2d\" is not a valid choice."]
}
```

#### `401 Unauthorized`

اگر کاربر لاگین نباشد.

---

## 5) GET /api/sensors/values-list/

### هدف

این endpoint لیست مقادیر current sensor و trend آن‌ها را برمی‌گرداند. مناسب برای card list، table کوتاه یا stat widgets است.

### احراز هویت

- نیازمند احراز هویت کاربر

### Query Params

| نام | نوع | اجباری | پیش‌فرض | توضیح |
|---|---|---:|---|---|
| `farm_uuid` | `uuid` | بله | - | شناسه مزرعه |
| `range` | `string` | خیر | `7d` | فقط `1h`، `24h` یا `7d` |

### نمونه درخواست

```http
GET /api/sensors/values-list/?farm_uuid=11111111-1111-1111-1111-111111111111&range=24h
Authorization: Bearer <access_token>
```

### پاسخ موفق

```json
{
  "sensors": [
    {
      "title": "Moisture",
      "subtitle": "مقدار فعلی: 48.5%",
      "trendNumber": 7.5,
      "trend": "positive",
      "unit": "%"
    },
    {
      "title": "Temperature",
      "subtitle": "مقدار فعلی: 23.2°C",
      "trendNumber": 2.2,
      "trend": "positive",
      "unit": "°C"
    },
    {
      "title": "PH",
      "subtitle": "مقدار فعلی: 6.8",
      "trendNumber": 0.3,
      "trend": "positive",
      "unit": "pH"
    }
  ]
}
```

### توضیح فیلدهای هر آیتم

| فیلد | نوع | توضیح |
|---|---|---|
| `title` | `string` | نام فیلد |
| `subtitle` | `string` | متن آماده برای نمایش مقدار فعلی |
| `trendNumber` | `number` | اختلاف آخرین مقدار نسبت به اولین مقدار در بازه |
| `trend` | `positive \| negative` | جهت تغییر |
| `unit` | `string` | واحد |

### نکات مهم فرانت

- `subtitle` از backend به‌صورت آماده برمی‌گردد.
- اگر در بازه انتخاب‌شده داده‌ای نباشد، backend آخرین لاگ موجود را fallback می‌کند.
- اگر هیچ لاگی وجود نداشته باشد:

```json
{
  "sensors": []
}
```

### خطاهای ممکن

#### `400 Bad Request`

اگر `range` نامعتبر باشد:

```json
{
  "range": ["\"12h\" is not a valid choice."]
}
```

#### `401 Unauthorized`

اگر کاربر لاگین نباشد.

---

## 6) GET /api/sensor-external-api/logs/

### هدف

این endpoint تاریخچه لاگ‌های ورودی سنسور خارجی را برمی‌گرداند. این API بیشتر برای:

- history page
- debugging panel
- raw sensor log table
- trace داده‌های دریافتی از device

مناسب است.

### احراز هویت

- نیازمند هدر `X-API-Key`

نمونه:

```http
X-API-Key: 12345
```

### Query Params

| نام | نوع | اجباری | توضیح |
|---|---|---:|---|
| `farm_uuid` | `uuid` | بله | شناسه مزرعه |
| `page` | `int` | بله | شماره صفحه، حداقل `1` |
| `page_size` | `int` | بله | اندازه صفحه، بین `1` تا `100` |
| `physical_device_uuid` | `uuid` | خیر | فیلتر روی دستگاه خاص |
| `sensor_type` | `string` | خیر | فیلتر روی نوع سنسور |
| `date_from` | `date` | خیر | فیلتر از تاریخ |
| `date_to` | `date` | خیر | فیلتر تا تاریخ |

### نمونه درخواست

```http
GET /api/sensor-external-api/logs/?farm_uuid=11111111-1111-1111-1111-111111111111&page=1&page_size=20
X-API-Key: 12345
```

نمونه با فیلتر:

```http
GET /api/sensor-external-api/logs/?farm_uuid=11111111-1111-1111-1111-111111111111&physical_device_uuid=55555555-5555-5555-5555-555555555555&date_from=2025-05-01&date_to=2025-05-10&page=1&page_size=20
X-API-Key: 12345
```

### پاسخ موفق

```json
{
  "code": 200,
  "msg": "success",
  "count": 2,
  "next": "http://example.com/api/sensor-external-api/logs/?farm_uuid=11111111-1111-1111-1111-111111111111&page=2&page_size=1",
  "previous": null,
  "data": [
    {
      "id": 12,
      "farm_uuid": "11111111-1111-1111-1111-111111111111",
      "sensor_catalog_uuid": "22222222-2222-2222-2222-222222222222",
      "physical_device_uuid": "55555555-5555-5555-5555-555555555555",
      "farm_sensor": {
        "uuid": "99999999-9999-9999-9999-999999999999",
        "sensor_catalog_uuid": "22222222-2222-2222-2222-222222222222",
        "physical_device_uuid": "55555555-5555-5555-5555-555555555555",
        "name": "External device 2",
        "sensor_type": "soil_sensor",
        "is_active": true,
        "specifications": {
          "model": "FH-2"
        },
        "power_source": {
          "type": "solar"
        },
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T10:00:00Z"
      },
      "sensor_catalog": {
        "uuid": "22222222-2222-2222-2222-222222222222",
        "code": "ext-sensor-log-2",
        "name": "External Sensor Log 2",
        "description": "Sensor catalog for second log",
        "customizable_fields": [],
        "supported_power_sources": [],
        "returned_data_fields": ["humidity"],
        "sample_payload": {},
        "is_active": true,
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T10:00:00Z"
      },
      "payload": {
        "temp": 18
      },
      "created_at": "2025-05-02T11:00:00Z"
    }
  ]
}
```

### توضیح فیلدهای ریشه پاسخ

| فیلد | نوع | توضیح |
|---|---|---|
| `code` | `number` | کد داخلی backend |
| `msg` | `string` | پیام |
| `count` | `number` | تعداد کل آیتم‌ها قبل از pagination |
| `next` | `string \| null` | لینک صفحه بعد |
| `previous` | `string \| null` | لینک صفحه قبل |
| `data` | `array` | داده‌های صفحه فعلی |

### توضیح هر آیتم داخل `data`

| فیلد | نوع | توضیح |
|---|---|---|
| `id` | `number` | شناسه لاگ |
| `farm_uuid` | `string` | UUID مزرعه |
| `sensor_catalog_uuid` | `string \| null` | UUID کاتالوگ سنسور |
| `physical_device_uuid` | `string` | UUID دستگاه |
| `farm_sensor` | `object \| null` | اطلاعات سنسور مزرعه |
| `sensor_catalog` | `object \| null` | اطلاعات catalog |
| `payload` | `object` | داده خام ارسالی از device |
| `created_at` | `string` | زمان ثبت لاگ |

### ساختار `farm_sensor`

| فیلد | نوع |
|---|---|
| `uuid` | `string` |
| `sensor_catalog_uuid` | `string \| null` |
| `physical_device_uuid` | `string` |
| `name` | `string` |
| `sensor_type` | `string` |
| `is_active` | `boolean` |
| `specifications` | `object` |
| `power_source` | `object` |
| `created_at` | `string` |
| `updated_at` | `string` |

### ساختار `sensor_catalog`

| فیلد | نوع |
|---|---|
| `uuid` | `string` |
| `code` | `string` |
| `name` | `string` |
| `description` | `string` |
| `customizable_fields` | `array` |
| `supported_power_sources` | `array` |
| `returned_data_fields` | `array` |
| `sample_payload` | `object` |
| `is_active` | `boolean` |
| `created_at` | `string` |
| `updated_at` | `string` |

### فیلترها

#### فیلتر با `physical_device_uuid`

فقط لاگ‌های مربوط به یک device خاص برمی‌گردد.

#### فیلتر با `sensor_type`

بر اساس `sensor_type` سنسور مزرعه فیلتر می‌کند.

#### فیلتر با `date_from` و `date_to`

بر اساس بازه تاریخ فیلتر می‌کند.

نکته:

- اگر هر دو ارسال شوند، `date_from` باید کوچک‌تر یا مساوی `date_to` باشد.

### خطاهای ممکن

#### `400 Bad Request`

اگر `page` یا `page_size` ارسال نشود:

```json
{
  "page": ["This field is required."],
  "page_size": ["This field is required."]
}
```

اگر `date_from > date_to` باشد:

```json
{
  "date_to": ["date_to must be greater than or equal to date_from."]
}
```

اگر `page_size > 100` باشد:

```json
{
  "page_size": ["Ensure this value is less than or equal to 100."]
}
```

#### `401 Unauthorized`

اگر API key وجود نداشته باشد:

```json
{
  "detail": "API key is required."
}
```

اگر API key اشتباه باشد:

```json
{
  "detail": "Invalid API key."
}
```

#### `503 Service Unavailable`

اگر migrationهای جدول‌های لازم اجرا نشده باشند:

```json
{
  "code": 503,
  "msg": "Required tables are not ready. Run migrations."
}
```

### نکات فرانت

- داده‌ها descending هستند؛ جدیدترین لاگ اول می‌آید.
- `farm_sensor` و `sensor_catalog` ممکن است `null` باشند.
- `payload` داینامیک است و ساختار ثابتی ندارد؛ UI باید generic باشد.
- برای table view بهتر است `payload` را stringify نکنید و فیلدهای مهم را extract کنید.
- برای pagination از `count`، `next` و `previous` استفاده کنید.

---

## 7) تفاوت مهم بین این APIها

| Endpoint | ساختار پاسخ | نیازمندی auth |
|---|---|---|
| `/api/sensor-7-in-1/summary/` | wrapped: `code/msg/data` | Bearer token / session |
| `/api/sensors/comparison-chart/` | raw json | Bearer token / session |
| `/api/sensors/radar-chart/` | raw json | Bearer token / session |
| `/api/sensors/values-list/` | raw json | Bearer token / session |
| `/api/sensor-external-api/logs/` | wrapped + paginated | `X-API-Key` |

---

## 8) پیشنهاد برای استفاده در فرانت

### برای dashboard اصلی

از `GET /api/sensor-7-in-1/summary/` استفاده کنید، چون بیشتر widgetها را یکجا می‌دهد.

### برای chartهای مستقل

- اگر chart جداگانه و lightweight می‌خواهید از:
  - `GET /api/sensors/comparison-chart/`
  - `GET /api/sensors/radar-chart/`

### برای stat card list

- از `GET /api/sensors/values-list/` استفاده کنید.

### برای page تاریخچه یا debug

- از `GET /api/sensor-external-api/logs/` استفاده کنید.

---

## 9) فایل‌های بک‌اند مرتبط

- `sensor_7_in_1/views.py`
- `sensor_7_in_1/serializers.py`
- `sensor_7_in_1/services.py`
- `sensor_7_in_1/tests.py`
- `sensor_external_api/views.py`
- `sensor_external_api/serializers.py`
- `sensor_external_api/tests.py`
- `sensor_external_api/authentication.py`

