# Water & Weather API Reference for Frontend

این فایل برای فرانت آماده شده تا ساختار پاسخ APIهای زیر مشخص باشد:

- `GET /api/water/card/`
- `GET /api/water/need-prediction/`
- `GET /api/water/summary/`
- `POST /api/weather/farm-card/`

## Base Notes

- `GET /api/water/card/` و `GET /api/water/summary/` بدون `farm_uuid` هم جواب می‌دهند.
- `GET /api/water/need-prediction/` هم بدون `farm_uuid` جواب می‌دهد، ولی اگر `farm_uuid` وجود داشته باشد ممکن است داده مزرعه‌محور برگردد.
- `POST /api/weather/farm-card/` نیاز به `farm_uuid` در body دارد.
- response shapeها بین این endpointها یکدست نیستند:
  - بعضی endpointها با `status/data`
  - بعضی endpointها با `code/msg/data`

---

## 1) Water Card

### Endpoint

```http
GET /api/water/card/?farm_uuid=<farm_uuid>
```

### Query Params

| field | type | required | description |
|---|---|---:|---|
| `farm_uuid` | `string (uuid)` | no | UUID مزرعه |

### Success Response

```json
{
  "status": "success",
  "data": {
    "condition": "صاف",
    "temperature": 24,
    "unit": "°C",
    "humidity": 45,
    "windSpeed": 12,
    "windUnit": "km/h",
    "chartData": {
      "labels": ["۶ صبح", "۹ صبح", "۱۲ ظهر", "۳ بعدازظهر"],
      "series": [[18, 22, 26, 28]]
    }
  }
}
```

### Response Fields

| field | type | description |
|---|---|---|
| `status` | `string` | در حالت موفق مقدار `success` |
| `data.condition` | `string` | وضعیت فعلی آب‌وهوا |
| `data.temperature` | `number` | دمای فعلی |
| `data.unit` | `string` | واحد دما |
| `data.humidity` | `number` | رطوبت نسبی |
| `data.windSpeed` | `number` | سرعت باد |
| `data.windUnit` | `string` | واحد سرعت باد |
| `data.chartData.labels` | `string[]` | برچسب‌های زمانی |
| `data.chartData.series` | `number[][]` | سری‌های نمودار |

### Frontend Notes

- این endpoint برای weather widget یا weather card مناسب است.
- `chartData.series` به شکل آرایه دوبعدی است.
- اگر `farm_uuid` ارسال شود، backend داده را از AI گرفته و log هم می‌کند.

---

## 2) Water Need Prediction

### Endpoint

```http
GET /api/water/need-prediction/?farm_uuid=<farm_uuid>
```

### Query Params

| field | type | required | description |
|---|---|---:|---|
| `farm_uuid` | `string (uuid)` | no | UUID مزرعه |

### Success Response

```json
{
  "status": "success",
  "data": {
    "farm_uuid": "11111111-1111-1111-1111-111111111111",
    "totalNext7Days": 24.6,
    "unit": "mm",
    "categories": ["2025-01-01", "2025-01-02", "2025-01-03"],
    "series": [
      {
        "name": "نیاز آبی",
        "data": [3.2, 4.1, 2.8]
      }
    ],
    "dailyBreakdown": [],
    "insight": {},
    "knowledge_base": "",
    "raw_response": ""
  }
}
```

### Response Fields

| field | type | description |
|---|---|---|
| `status` | `string` | در حالت موفق مقدار `success` |
| `data.farm_uuid` | `string` | UUID مزرعه در حالت farm-based |
| `data.totalNext7Days` | `number` | مجموع نیاز آبی 7 روز آینده |
| `data.unit` | `string` | واحد نیاز آبی، مثل `mm` یا `m3` |
| `data.categories` | `string[]` | روزها یا تاریخ‌ها |
| `data.series` | `Array<{name: string, data: number[]}>` | داده‌های نمودار |
| `data.dailyBreakdown` | `object[]` | breakdown روزانه در صورت وجود |
| `data.insight` | `object` | insight یا خلاصه تحلیلی |
| `data.knowledge_base` | `string` | منبع دانشی در صورت وجود |
| `data.raw_response` | `string` | پاسخ خام upstream در صورت وجود |

### Frontend Notes

- اگر `farm_uuid` معتبر باشد، backend داده را از AI می‌گیرد.
- اگر `farm_uuid` ارسال نشود، backend از داده داخلی/mock استفاده می‌کند.
- اگر `farm_uuid` ارسال شود ولی مزرعه پیدا نشود، فعلاً به fallback داخلی برمی‌گردد و خطا نمی‌دهد.

---

## 3) Water Summary

### Endpoint

```http
GET /api/water/summary/?farm_uuid=<farm_uuid>
```

### Query Params

| field | type | required | description |
|---|---|---:|---|
| `farm_uuid` | `string (uuid)` | no | UUID مزرعه |

### Success Response

```json
{
  "status": "success",
  "data": {
    "farmWeatherCard": {
      "condition": "صاف",
      "temperature": 24,
      "unit": "°C",
      "humidity": 45,
      "windSpeed": 12,
      "windUnit": "km/h",
      "chartData": {
        "labels": ["۶ صبح", "۹ صبح", "۱۲ ظهر"],
        "series": [[18, 22, 26]]
      }
    },
    "waterNeedPrediction": {
      "totalNext7Days": 3290,
      "unit": "m3",
      "categories": ["روز 1", "روز 2", "روز 3"],
      "series": [
        {
          "name": "نیاز آبی",
          "data": [420, 450, 480]
        }
      ]
    },
    "waterStressIndex": {
      "id": "water_stress_index",
      "title": "شاخص تنش آبی",
      "subtitle": "فعلی",
      "stats": "12%",
      "avatarColor": "info",
      "avatarIcon": "tabler-droplet",
      "chipText": "پایین",
      "chipColor": "success"
    }
  }
}
```

### Response Fields

| field | type | description |
|---|---|---|
| `status` | `string` | در حالت موفق مقدار `success` |
| `data.farmWeatherCard` | `object` | اطلاعات کارت وضعیت آب‌وهوا |
| `data.waterNeedPrediction` | `object` | پیش‌بینی نیاز آبی |
| `data.waterStressIndex` | `object` | کارت شاخص تنش آبی |

### `waterStressIndex` Fields

| field | type | description |
|---|---|---|
| `id` | `string` | شناسه کارت |
| `title` | `string` | عنوان کارت |
| `subtitle` | `string` | زیرعنوان |
| `stats` | `string` | مقدار اصلی برای نمایش |
| `avatarColor` | `string` | رنگ کارت/آیکن |
| `avatarIcon` | `string` | نام آیکن |
| `chipText` | `string` | وضعیت متنی |
| `chipColor` | `string` | رنگ وضعیت |

### Frontend Notes

- این endpoint برای dashboard overview مناسب است.
- سه بخش اصلی summary را می‌توانید مستقیم به سه widget مختلف map کنید.
- `waterSummary` یک response ترکیبی است و برای یک صفحه dashboard خیلی کاربردی است.

---

## 4) Weather Farm Card

### Endpoint

```http
POST /api/weather/farm-card/
```

### Request Body

```json
{
  "farm_uuid": "11111111-1111-1111-1111-111111111111"
}
```

### Request Fields

| field | type | required | description |
|---|---|---:|---|
| `farm_uuid` | `string (uuid)` | yes | UUID مزرعه |

### Success Response

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "condition": "صاف",
    "temperature": 28.0,
    "unit": "°C",
    "humidity": 45,
    "windSpeed": 12,
    "windUnit": "km/h",
    "chartData": {
      "labels": ["۶ صبح", "۹ صبح", "۱۲ ظهر", "۳ بعدازظهر"],
      "series": [[18, 22, 26, 28]]
    }
  }
}
```

### Response Fields

| field | type | description |
|---|---|---|
| `code` | `number` | در حالت موفق مقدار `200` |
| `msg` | `string` | در حالت موفق مقدار `success` |
| `data.condition` | `string` | وضعیت فعلی آب‌وهوا |
| `data.temperature` | `number` | دمای فعلی |
| `data.unit` | `string` | واحد دما |
| `data.humidity` | `number` | رطوبت نسبی |
| `data.windSpeed` | `number` | سرعت باد |
| `data.windUnit` | `string` | واحد سرعت باد |
| `data.chartData.labels` | `string[]` | برچسب‌های زمانی |
| `data.chartData.series` | `number[][]` | داده‌های نمودار |

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

### Error Response - Upstream Error

```json
{
  "code": 500,
  "msg": "error",
  "data": {
    "message": "Upstream service error"
  }
}
```

### Frontend Notes

- این endpoint نسخه authenticated و farm-specific برای weather card است.
- اگر farm متعلق به کاربر فعلی نباشد، `404` برمی‌گردد.
- response این endpoint با `code/msg/data` است، نه `status/data`.

---

## Suggested TypeScript Interfaces

```ts
export interface WeatherChartData {
  labels?: string[];
  series?: number[][];
}

export interface FarmWeatherCard {
  condition?: string;
  temperature?: number;
  unit?: string;
  humidity?: number;
  windSpeed?: number;
  windUnit?: string;
  chartData?: WeatherChartData;
}

export interface WaterNeedSeries {
  name?: string;
  data?: number[];
}

export interface WaterNeedPrediction {
  farm_uuid?: string;
  totalNext7Days?: number;
  unit?: string;
  categories?: string[];
  series?: WaterNeedSeries[];
  dailyBreakdown?: Record<string, unknown>[];
  insight?: Record<string, unknown>;
  knowledge_base?: string;
  raw_response?: string;
}

export interface WaterStressCard {
  id?: string;
  title?: string;
  subtitle?: string;
  stats?: string;
  avatarColor?: string;
  avatarIcon?: string;
  chipText?: string;
  chipColor?: string;
}
```

---

## Suggested Frontend Handling

- برای `GET /api/water/card/`, `GET /api/water/need-prediction/`, `GET /api/water/summary/` انتظار `status/data` داشته باشید.
- برای `POST /api/weather/farm-card/` انتظار `code/msg/data` داشته باشید.
- برای `POST /api/weather/farm-card/` خطاها را از `data.farm_uuid[0]` بخوانید.
- برای chartها بهتر است `labels` و `series` را optional render کنید.
