# راهنمای API فرانت برای سنسورها

این فایل برای تحویل به فرانت نوشته شده و دو app را به‌صورت جداگانه توضیح می‌دهد:

1. `sensor_external_api`
2. `sensor_7_in_1`

---

# صفحه 1 - `sensor_external_api`

## اطلاعات app

- فایل app: `sensor_external_api/apps.py`
- AppConfig: `SensorExternalApiConfig`
- Django app name: `sensor_external_api`
- Base URL: `/api/sensor-external-api/`

## کاربرد این app

این app برای دریافت payload خام از سنسور خارجی و همچنین مشاهده لاگ‌های ثبت‌شده آن استفاده می‌شود.

نکته مهم:

- endpoint ثبت payload بیشتر برای **خود سنسور / gateway / backend integration** است.
- endpoint لاگ‌ها برای **فرانت** مناسب است تا آخرین داده‌های خام دریافت‌شده را ببیند.

## API 1 - ثبت payload از سنسور خارجی

- Method: `POST`
- URL: `/api/sensor-external-api/`
- Auth: هدر `X-API-Key`
- Permission: عمومی است، ولی فقط با API key معتبر

### Header

```http
X-API-Key: 12345
Content-Type: application/json
```

### Body

```json
{
  "uuid": "33333333-3333-3333-3333-333333333333",
  "payload": {
    "soil_moisture": 48.5,
    "soil_temperature": 23.2,
    "soil_ph": 6.8,
    "electrical_conductivity": 1.4,
    "nitrogen": 31,
    "phosphorus": 16,
    "potassium": 24
  }
}
```

### توضیح فیلدها

- `uuid`: شناسه فیزیکی دستگاه سنسور
- `payload`: داده خام ارسال‌شده توسط دستگاه

### پاسخ موفق

```json
{
  "code": 201,
  "msg": "success",
  "data": {
    "id": 1,
    "title": "Sensor external API request",
    "message": "Payload received from device 33333333-3333-3333-3333-333333333333."
  }
}
```

### خطاهای مهم

- `401`: API key نامعتبر یا ارسال نشده
- `404`: سنسور با این `uuid` پیدا نشده
- `503`: سرویس مقصد یا جداول موردنیاز آماده نیستند

## API 2 - دریافت لاگ‌های سنسور خارجی

- Method: `GET`
- URL: `/api/sensor-external-api/logs/?farm_uuid=<uuid>`
- Auth: JWT کاربر
- Permission: `IsAuthenticated`

### Query Params

- `farm_uuid` اجباری
- `page` اختیاری
- `page_size` اختیاری

### نمونه درخواست

```http
GET /api/sensor-external-api/logs/?farm_uuid=11111111-1111-1111-1111-111111111111&page=1&page_size=20
Authorization: Bearer <token>
```

### پاسخ موفق

```json
{
  "code": 200,
  "msg": "success",
  "count": 2,
  "next": null,
  "previous": null,
  "data": [
    {
      "id": 10,
      "farm_uuid": "11111111-1111-1111-1111-111111111111",
      "sensor_catalog_uuid": "22222222-2222-2222-2222-222222222222",
      "physical_device_uuid": "33333333-3333-3333-3333-333333333333",
      "farm_sensor": {
        "uuid": "aaaa1111-1111-1111-1111-111111111111",
        "sensor_catalog_uuid": "22222222-2222-2222-2222-222222222222",
        "physical_device_uuid": "33333333-3333-3333-3333-333333333333",
        "name": "Soil Sensor 7-in-1",
        "sensor_type": "soil_7_in_1",
        "is_active": true,
        "specifications": {},
        "power_source": {},
        "created_at": "2025-03-24T10:00:00Z",
        "updated_at": "2025-03-24T10:00:00Z"
      },
      "sensor_catalog": {
        "uuid": "22222222-2222-2222-2222-222222222222",
        "code": "sensor-7-in-1",
        "name": "7 in 1 Soil Sensor",
        "description": "",
        "customizable_fields": [],
        "supported_power_sources": [],
        "returned_data_fields": [
          "soil_moisture",
          "soil_temperature",
          "soil_ph",
          "electrical_conductivity",
          "nitrogen",
          "phosphorus",
          "potassium"
        ],
        "sample_payload": {},
        "is_active": true,
        "created_at": "2025-03-24T10:00:00Z",
        "updated_at": "2025-03-24T10:00:00Z"
      },
      "payload": {
        "soil_moisture": 48.5,
        "soil_temperature": 23.2,
        "soil_ph": 6.8,
        "electrical_conductivity": 1.4,
        "nitrogen": 31,
        "phosphorus": 16,
        "potassium": 24
      },
      "created_at": "2025-03-24T10:00:00Z"
    }
  ]
}
```

## کاربرد فرانت

- برای صفحه history / logs سنسور
- برای نمایش raw payload دریافتی از دستگاه
- برای debug و بررسی آخرین داده‌های ثبت‌شده

## نکته فرانت

برای نمایش کارت‌های نهایی و تمیزشده سنسور 7 در 1 بهتر است از app بعدی یعنی `sensor_7_in_1` استفاده شود، نه از payload خام این app.

---

# صفحه 2 - `sensor_7_in_1`

## اطلاعات app

- فایل app: `sensor_7_in_1/apps.py`
- AppConfig: `Sensor7In1Config`
- Django app name: `sensor_7_in_1`
- Base URL: `/api/sensor-7-in-1/`
- Feature code: `sensor-7-in-1`

## کاربرد این app

این app داده‌های خام ثبت‌شده در `sensor_external_api` را می‌خواند و فقط اطلاعات مربوط به **یک سنسور خاص** یعنی سنسور خاک 7-in-1 را به فرم قابل‌استفاده برای UI برمی‌گرداند.

به‌جای اینکه فرانت خودش از payload خام `soil_moisture`, `soil_ph`, `nitrogen` و ... کارت بسازد، این app خروجی نهایی UI-ready می‌دهد.

## API اصلی

- Method: `GET`
- URL: `/api/sensor-7-in-1/summary/?farm_uuid=<uuid>`
- Auth: JWT کاربر
- Permission: `IsAuthenticated`

### Query Params

- `farm_uuid` اجباری

### نمونه درخواست

```http
GET /api/sensor-7-in-1/summary/?farm_uuid=11111111-1111-1111-1111-111111111111
Authorization: Bearer <token>
```

### پاسخ موفق

```json
{
  "code": 200,
  "msg": "OK",
  "data": {
    "sensor": {
      "name": "Soil Sensor 7-in-1",
      "physicalDeviceUuid": "33333333-3333-3333-3333-333333333333",
      "sensorCatalogCode": "sensor-7-in-1",
      "updatedAt": "2025-03-24T10:00:00Z"
    },
    "sensorValuesList": {
      "sensor": {
        "name": "Soil Sensor 7-in-1",
        "physicalDeviceUuid": "33333333-3333-3333-3333-333333333333",
        "sensorCatalogCode": "sensor-7-in-1",
        "updatedAt": "2025-03-24T10:00:00Z"
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
          "data": [87, 90, 95, 88, 90, 85, 92]
        },
        {
          "name": "هدف",
          "data": [100, 100, 100, 100, 100, 100, 100]
        }
      ]
    },
    "sensorComparisonChart": {
      "currentValue": 48.5,
      "vsLastWeek": "+18.3%",
      "vsLastWeekValue": 18.3,
      "categories": ["03/24 09:00", "03/24 10:00"],
      "series": [
        {
          "name": "رطوبت خاک",
          "data": [41, 48.5]
        },
        {
          "name": "بازه هدف",
          "data": [55, 55]
        }
      ]
    },
    "anomalyDetectionCard": {
      "anomalies": [
        {
          "sensor": "هدایت الکتریکی",
          "value": "1.4 dS/m",
          "expected": "0.8-1.8 dS/m",
          "deviation": "0",
          "severity": "success"
        }
      ]
    },
    "soilMoistureHeatmap": {
      "zones": ["Soil Sensor 7-in-1"],
      "hours": ["09:00", "10:00"],
      "series": [
        {
          "name": "Soil Sensor 7-in-1",
          "data": [
            { "x": "09:00", "y": 41 },
            { "x": "10:00", "y": 48.5 }
          ]
        }
      ]
    }
  }
}
```

## فیلدهای مهم برای فرانت

### `sensor`

اطلاعات شناسایی سنسور:

- `name`
- `physicalDeviceUuid`
- `sensorCatalogCode`
- `updatedAt`

### `sensorValuesList`

برای لیست کارت‌های عددی سنسور:

- رطوبت خاک
- دمای خاک
- pH خاک
- هدایت الکتریکی
- نیتروژن
- فسفر
- پتاسیم

### `avgSoilMoisture`

برای KPI رطوبت خاک در dashboard

### `sensorRadarChart`

برای نمودار radar وضعیت شاخص‌های سنسور

### `sensorComparisonChart`

برای نمودار روند رطوبت خاک نسبت به داده‌های قبلی

### `anomalyDetectionCard`

برای نمایش مقادیر خارج از بازه نرمال

### `soilMoistureHeatmap`

برای heatmap یا نمودار تاریخچه رطوبت خاک

## رفتار این app

- فقط داده سنسوری را که مشخصات 7-in-1 داشته باشد برمی‌گرداند
- داده‌ها را از لاگ‌های `sensor_external_api` می‌خواند
- اگر داده واقعی پیدا نشود، fallback mock برمی‌گرداند
- این app همان منبعی است که dashboard برای کارت‌های سنسوری از آن استفاده می‌کند

## پیشنهاد استفاده در فرانت

- اگر هدف نمایش **کارت‌های نهایی سنسور** است، از `sensor_7_in_1` استفاده کنید
- اگر هدف نمایش **لاگ خام payload** یا history ورودی دستگاه است، از `sensor_external_api/logs/` استفاده کنید

