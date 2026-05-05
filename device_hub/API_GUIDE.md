# Device Hub API Guide

این فایل مستند API های تعریف‌شده در `device_hub/urls.py` را توضیح می‌دهد. مسیر پایه این API ها طبق `config/urls.py` برابر است با:

- `api/device-hub/`

بیشتر endpointها نیاز به احراز هویت کاربر دارند و معمولاً با ساختار زیر پاسخ می‌دهند:

```json
{
  "code": 200,
  "msg": "success",
  "data": {}
}
```

## نحوه ارتباط با API ها

### 1) احراز هویت

- برای بیشتر endpointها باید کاربر لاگین باشد.
- معمولاً توکن را در هدر `Authorization` ارسال می‌کنید.
- نمونه:

```http
Authorization: Bearer <token>
Content-Type: application/json
```

### 2) آدرس پایه

اگر دامنه پروژه مثلاً `https://example.com` باشد، آدرس کامل endpointها به این صورت است:

- `https://example.com/api/device-hub/catalog/`
- `https://example.com/api/device-hub/devices/<physical_device_uuid>/latest/?device_code=<code>`

### 3) پارامترهای مهم

- `physical_device_uuid`: شناسه فیزیکی دستگاه
- `device_code`: کد نوع device داخل catalog
- `range`: بازه زمانی (`1h`, `24h`, `7d`, `30d`, `today` بسته به endpoint)
- `page` و `page_size`: برای صفحه‌بندی لاگ‌ها

---

## 1. دریافت لیست کاتالوگ دستگاه‌ها

### Endpoint

- `GET /api/device-hub/catalog/`
- `GET /api/device-hub/`

### کاربرد

برای گرفتن لیست همه device catalogها استفاده می‌شود.

### درخواست نمونه

```bash
curl -X GET "https://example.com/api/device-hub/catalog/" \
  -H "Authorization: Bearer <token>"
```

### پاسخ نمونه

```json
{
  "code": 200,
  "msg": "success",
  "data": [
    {
      "uuid": "11111111-1111-1111-1111-111111111111",
      "code": "soil_sensor_v2",
      "name": "Soil Sensor V2",
      "description": "",
      "device_communication_type": "output_only",
      "customizable_fields": [],
      "supported_power_sources": [],
      "returned_data_fields": ["soil_moisture", "soil_temperature"],
      "payload_mapping": {
        "soil_moisture": ["moisture", "soil_moisture"],
        "soil_temperature": ["temperature", "soil_temperature"]
      },
      "display_schema": {},
      "supported_widgets": ["values_list", "comparison_chart", "radar_chart"],
      "commands_schema": [],
      "capabilities": [],
      "sample_payload": {},
      "is_active": true
    }
  ]
}
```

### فیلدهای مهم پاسخ

- `device_communication_type`: نوع ارتباط دستگاه (`output_only` یا `input_only`)
- `returned_data_fields`: داده‌هایی که device برمی‌گرداند
- `payload_mapping`: نگاشت کلیدهای payload خام به فیلدهای نرمال
- `supported_widgets`: ویجت‌هایی که فرانت می‌تواند نمایش دهد
- `commands_schema`: لیست commandهای قابل ارسال برای deviceهای commandable

---

## 2. جزئیات یک دستگاه

### Endpoint

- `GET /api/device-hub/devices/<physical_device_uuid>/?device_code=<device_code>`

### کاربرد

اطلاعات کلی دستگاه ثبت‌شده در فارم را برمی‌گرداند.

### Query Params

- `device_code` اجباری

### درخواست نمونه

```bash
curl -X GET "https://example.com/api/device-hub/devices/22222222-2222-2222-2222-222222222222/?device_code=soil_sensor_v2" \
  -H "Authorization: Bearer <token>"
```

### پاسخ نمونه

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "uuid": "33333333-3333-3333-3333-333333333333",
    "physical_device_uuid": "22222222-2222-2222-2222-222222222222",
    "name": "Soil Device 1",
    "sensor_type": "soil",
    "is_active": true,
    "specifications": {},
    "power_source": {},
    "device_catalog": {
      "uuid": "11111111-1111-1111-1111-111111111111",
      "code": "soil_sensor_v2",
      "name": "Soil Sensor V2",
      "description": "",
      "device_communication_type": "output_only",
      "customizable_fields": [],
      "supported_power_sources": [],
      "returned_data_fields": ["soil_moisture", "soil_temperature"],
      "payload_mapping": {},
      "display_schema": {},
      "supported_widgets": ["values_list", "comparison_chart", "radar_chart"],
      "commands_schema": [],
      "capabilities": [],
      "sample_payload": {},
      "is_active": true
    },
    "device_catalogs": [],
    "last_payload_at": "2025-01-01T10:00:00Z",
    "created_at": "2025-01-01T09:00:00Z",
    "updated_at": "2025-01-01T09:00:00Z"
  }
}
```

### نکته

- اگر `physical_device_uuid` متعلق به کاربر نباشد، خطای 400 با متن `Device not found.` برمی‌گردد.
- اگر `device_code` به این دستگاه attach نشده باشد، خطای validation دریافت می‌کنید.

---

## 3. آخرین payload دستگاه

### Endpoint

- `GET /api/device-hub/devices/<physical_device_uuid>/latest/?device_code=<device_code>`

### کاربرد

آخرین payload خام و نرمال‌شده دستگاه را می‌دهد.

### Query Params

- `device_code` اجباری

### پاسخ نمونه

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "physical_device_uuid": "22222222-2222-2222-2222-222222222222",
    "device_code": "soil_sensor_v2",
    "device_catalog_code": "soil_sensor_v2",
    "raw_payload": {
      "moisture": 52.4,
      "temperature": 23.1
    },
    "normalized_payload": {
      "soil_moisture": 52.4,
      "soil_temperature": 23.1
    },
    "readings": {
      "soil_moisture": 52.4,
      "soil_temperature": 23.1
    },
    "created_at": "2025-01-01T10:00:00Z"
  }
}
```

### معنی فیلدها

- `raw_payload`: داده خامی که از لاگ ذخیره‌شده آمده
- `normalized_payload`: داده تبدیل‌شده بر اساس `payload_mapping`
- `readings`: مقادیر قابل نمایش برای UI

---

## 4. خلاصه دستگاه

### Endpoint

- `GET /api/device-hub/devices/<physical_device_uuid>/summary/?device_code=<device_code>`

### کاربرد

یک summary مناسب UI برمی‌گرداند؛ مثلاً ویجت‌های قابل نمایش، values list، chartها و commandها.

### Query Params

- `device_code` اجباری

### پاسخ نمونه

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "sensor": {
      "name": "Soil Device 1",
      "physicalDeviceUuid": "22222222-2222-2222-2222-222222222222",
      "sensorCatalogCode": "soil_sensor_v2",
      "updatedAt": "2025-01-01T10:00:00Z"
    },
    "supportedWidgets": ["values_list", "comparison_chart", "radar_chart"],
    "sensorValuesList": {
      "sensor": {
        "name": "Soil Device 1",
        "physicalDeviceUuid": "22222222-2222-2222-2222-222222222222",
        "sensorCatalogCode": "soil_sensor_v2",
        "updatedAt": "2025-01-01T10:00:00Z"
      },
      "sensors": [
        {
          "id": "soil_moisture",
          "title": "رطوبت خاک",
          "subtitle": "45-65%",
          "trendNumber": 52.4,
          "trend": "normal",
          "unit": "%"
        }
      ]
    },
    "commands": []
  }
}
```

### نکته

- شکل دقیق `data` بسته به `supported_widgets` و نوع catalog تغییر می‌کند.
- اگر history وجود نداشته باشد، معمولاً خطای 400 برمی‌گردد.

---

## 5. نمودار مقایسه‌ای دستگاه

### Endpoint

- `GET /api/device-hub/devices/<physical_device_uuid>/comparison-chart/?device_code=<device_code>&range=7d`

### Query Params

- `device_code` اجباری
- `range` اختیاری: `7d` یا `30d`

### پاسخ نمونه

```json
{
  "series": [
    {
      "name": "Moisture",
      "data": [50.0, 51.2, 52.4]
    },
    {
      "name": "Temperature",
      "data": [22.0, 22.4, 23.1]
    }
  ],
  "categories": ["شنبه", "یکشنبه", "دوشنبه"],
  "currentValue": 52.4,
  "vsLastWeek": "+3.1%"
}
```

### نکته

- این endpoint برخلاف بعضی endpointهای دیگر wrapper `code/msg` ندارد و مستقیم data chart را برمی‌گرداند.

---

## 6. لیست مقادیر دستگاه

### Endpoint

- `GET /api/device-hub/devices/<physical_device_uuid>/values-list/?device_code=<device_code>&range=7d`

### Query Params

- `device_code` اجباری
- `range` اختیاری: `1h`، `24h`، `7d`

### پاسخ نمونه

```json
{
  "sensors": [
    {
      "title": "Moisture",
      "subtitle": "45-65%",
      "trendNumber": 52.4,
      "trend": "positive",
      "unit": "%"
    },
    {
      "title": "Temperature",
      "subtitle": "18-28°C",
      "trendNumber": 23.1,
      "trend": "positive",
      "unit": "°C"
    }
  ]
}
```

### نکته

- این endpoint هم مستقیم JSON داده را برمی‌گرداند و wrapper `code/msg` ندارد.

---

## 7. رادار چارت دستگاه

### Endpoint

- `GET /api/device-hub/devices/<physical_device_uuid>/radar-chart/?device_code=<device_code>&range=7d`

### Query Params

- `device_code` اجباری
- `range` اختیاری: `today`، `7d`، `30d`

### پاسخ نمونه

```json
{
  "labels": ["Moisture", "Temperature", "PH", "EC"],
  "series": [
    {
      "name": "Current",
      "data": [52.4, 23.1, 6.7, 1.1]
    }
  ]
}
```

### نکته

- این endpoint هم مستقیم data را برمی‌گرداند.

---

## 8. لاگ‌های دستگاه

### Endpoint

- `GET /api/device-hub/devices/<physical_device_uuid>/logs/?device_code=<device_code>&page=1&page_size=20`

### Query Params

- `device_code` اجباری
- `page` اختیاری، پیش‌فرض `1`
- `page_size` اختیاری، پیش‌فرض `20`، حداکثر `100`

### پاسخ نمونه

```json
{
  "code": 200,
  "msg": "success",
  "count": 1,
  "next": null,
  "previous": null,
  "data": [
    {
      "id": 10,
      "farm_uuid": "44444444-4444-4444-4444-444444444444",
      "sensor_catalog_uuid": "11111111-1111-1111-1111-111111111111",
      "physical_device_uuid": "22222222-2222-2222-2222-222222222222",
      "farm_device": {
        "uuid": "33333333-3333-3333-3333-333333333333",
        "sensor_catalog_uuid": "11111111-1111-1111-1111-111111111111",
        "device_catalogs": [],
        "physical_device_uuid": "22222222-2222-2222-2222-222222222222",
        "name": "Soil Device 1",
        "sensor_type": "soil",
        "is_active": true,
        "specifications": {},
        "power_source": {},
        "created_at": "2025-01-01T09:00:00Z",
        "updated_at": "2025-01-01T09:00:00Z"
      },
      "sensor_catalog": {
        "uuid": "11111111-1111-1111-1111-111111111111",
        "code": "soil_sensor_v2",
        "name": "Soil Sensor V2",
        "description": "",
        "device_communication_type": "output_only",
        "customizable_fields": [],
        "supported_power_sources": [],
        "returned_data_fields": [],
        "payload_mapping": {},
        "display_schema": {},
        "supported_widgets": [],
        "commands_schema": [],
        "capabilities": [],
        "sample_payload": {},
        "is_active": true,
        "created_at": "2025-01-01T09:00:00Z",
        "updated_at": "2025-01-01T09:00:00Z"
      },
      "payload": {
        "moisture": 52.4,
        "temperature": 23.1
      },
      "created_at": "2025-01-01T10:00:00Z"
    }
  ]
}
```

### کاربرد

- برای history دستگاه
- برای نمایش payloadهای دریافت‌شده از device
- برای debug یا audit

---

## 9. ارسال command به دستگاه

### Endpoint

- `POST /api/device-hub/devices/<physical_device_uuid>/commands/`

### کاربرد

برای deviceهایی که `input_only` یا commandable هستند، command ارسال می‌کند.

### Body

```json
{
  "device_code": "valve_v1",
  "command": "open",
  "payload": {
    "duration_seconds": 120
  }
}
```

### درخواست نمونه

```bash
curl -X POST "https://example.com/api/device-hub/devices/22222222-2222-2222-2222-222222222222/commands/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "device_code": "valve_v1",
    "command": "open",
    "payload": {
      "duration_seconds": 120
    }
  }'
```

### پاسخ نمونه

```json
{
  "code": 200,
  "msg": "command accepted",
  "data": {
    "physical_device_uuid": "22222222-2222-2222-2222-222222222222",
    "command": "open",
    "status": "accepted"
  }
}
```

### نکات

- `device_code` باید جزو catalogهای متصل به آن device باشد.
- اگر command یا device code معتبر نباشد، خطای 400 برمی‌گردد.

---

## 10. خلاصه سنسور 7in1

### Endpoint

- `GET /api/device-hub/summary/?farm_uuid=<farm_uuid>`

### کاربرد

خلاصه‌ای از سنسور اصلی مزرعه برای UI برمی‌گرداند.

### Query Params

- `farm_uuid` اجباری

### پاسخ نمونه

```json
{
  "code": 200,
  "msg": "OK",
  "data": {
    "sensor": {
      "name": "Main Soil Sensor",
      "physicalDeviceUuid": "22222222-2222-2222-2222-222222222222",
      "sensorCatalogCode": "sensor-7-in-1",
      "updatedAt": "2025-01-01T10:00:00Z"
    },
    "sensorValuesList": {},
    "avgSoilMoisture": {},
    "sensorRadarChart": {},
    "sensorComparisonChart": {},
    "anomalyDetectionCard": {},
    "soilMoistureHeatmap": {}
  }
}
```

---

## 11. ثبت payload خارجی دستگاه

### Endpoint

- `POST /api/device-hub/external/`

### کاربرد

این endpoint برای سیستم یا دستگاه خارجی است تا payload را به backend ارسال کند.  
این endpoint با API key اختصاصی کار می‌کند، نه با توکن کاربر.

### Header

```http
X-API-Key: <api_key>
Content-Type: application/json
```

### Body

```json
{
  "uuid": "22222222-2222-2222-2222-222222222222",
  "payload": {
    "moisture_percent": 32.5,
    "temperature_c": 21.3,
    "ph": 6.7,
    "ec_ds_m": 1.1,
    "nitrogen_mg_kg": 42,
    "phosphorus_mg_kg": 18,
    "potassium_mg_kg": 210
  }
}
```

### رفتار endpoint

- payload را در `SensorExternalRequestLog` ذخیره می‌کند
- notification می‌سازد
- payload را به farm-data service فوروارد می‌کند

### پاسخ موفق نمونه

```json
{
  "code": 201,
  "msg": "success",
  "data": {
    "id": 1,
    "title": "Sensor external API request"
  }
}
```

### خطاهای مهم

- `401`: اگر `X-API-Key` اشتباه یا خالی باشد
- `404`: اگر `physical device` پیدا نشود
- `503`: اگر migrationها آماده نباشند یا سرویس farm-data در دسترس نباشد

---

## 12. لیست لاگ‌های ورودی خارجی

### Endpoint

- `GET /api/device-hub/external/logs/?farm_uuid=<farm_uuid>&page=1&page_size=20`

### Query Params

- `farm_uuid` اجباری
- `page` اجباری در داکیومنت، ولی در عمل اگر نفرستید پیش‌فرض `1` دارد در paginator
- `page_size` اجباری در داکیومنت
- `physical_device_uuid` اختیاری
- `sensor_type` اختیاری
- `date_from` اختیاری
- `date_to` اختیاری

### پاسخ نمونه

```json
{
  "code": 200,
  "msg": "success",
  "count": 25,
  "next": "https://example.com/api/device-hub/external/logs/?page=2",
  "previous": null,
  "data": [
    {
      "id": 10,
      "farm_uuid": "44444444-4444-4444-4444-444444444444",
      "sensor_catalog_uuid": "11111111-1111-1111-1111-111111111111",
      "physical_device_uuid": "22222222-2222-2222-2222-222222222222",
      "farm_device": null,
      "sensor_catalog": null,
      "payload": {
        "moisture": 52.4
      },
      "created_at": "2025-01-01T10:00:00Z"
    }
  ]
}
```

---

## الگوی خطاها

### Validation Error

در بیشتر خطاهای اعتبارسنجی، پاسخ شبیه این است:

```json
{
  "device_code": [
    "Device code is not attached to this farm device."
  ]
}
```
یا:

```json
{
  "physical_device_uuid": [
    "Device not found."
  ]
}
```

### Unauthorized

اگر توکن کاربر یا API key درست نباشد، پاسخ 401 دریافت می‌کنید.

### Service Unavailable

در endpointهای `external` اگر migration یا سرویس وابسته آماده نباشد:

```json
{
  "code": 503,
  "msg": "Required tables are not ready. Run migrations."
}
```

---

## ترتیب پیشنهادی استفاده در فرانت

برای صفحه جزئیات device معمولاً این ترتیب مناسب است:

1. گرفتن catalogها از `GET /api/device-hub/catalog/`
2. گرفتن جزئیات device از `GET /api/device-hub/devices/<uuid>/?device_code=...`
3. گرفتن summary از `GET /api/device-hub/devices/<uuid>/summary/?device_code=...`
4. در صورت نیاز گرفتن:
   - latest payload
   - comparison chart
   - radar chart
   - values list
   - logs

برای deviceهای commandable:

1. از `commands_schema` در catalog commandهای مجاز را بخوانید
2. سپس به `POST /api/device-hub/devices/<uuid>/commands/` درخواست بزنید

---

## محل فایل‌های مرتبط در کد

- مسیرها: `device_hub/urls.py`
- ویوها: `device_hub/views.py`
- serializerها: `device_hub/serializers.py`
- serializerهای summary/chart: `device_hub/sensor_serializers.py`
- مسیر پایه پروژه: `config/urls.py`
