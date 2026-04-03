# مستندات کامل API های `farm_hub`

این فایل بر اساس پیاده‌سازی واقعی اپ `farm_hub` در فایل‌های `farm_hub/urls.py`, `farm_hub/views.py`, `farm_hub/serializers.py`, `farm_hub/models.py` و `farm_hub/services.py` تهیه شده است.

نکته مهم: فایل `farm_hub/apps.py` فقط برای ثبت Django app استفاده می‌شود و خودِ APIها داخل آن تعریف نشده‌اند. APIهای این ماژول در `farm_hub/urls.py` و `farm_hub/views.py` قرار دارند.

## مشخصات کلی

- Base path:

```text
/api/farm-hub/
```

- احراز هویت:

تمام endpointهای این ماژول نیاز به کاربر لاگین‌شده دارند.

```http
Authorization: Bearer <token>
```

- فرمت کلی پاسخ موفق:

```json
{
  "code": 200,
  "msg": "success",
  "data": {}
}
```

- فرمت کلی پاسخ خطا:

```json
{
  "code": 404,
  "msg": "Farm not found."
}
```

یا در خطاهای validation:

```json
{
  "field_name": [
    "error message"
  ]
}
```

## لیست endpointها

| Method | URL | توضیح |
|---|---|---|
| GET | `/api/farm-hub/` | دریافت لیست مزارع کاربر جاری |
| POST | `/api/farm-hub/` | ساخت مزرعه جدید |
| GET | `/api/farm-hub/farm-types/` | دریافت لیست نوع مزرعه‌ها |
| GET | `/api/farm-hub/farm-types/{farm_type_uuid}/products/` | دریافت محصولات مربوط به یک نوع مزرعه |
| GET | `/api/farm-hub/{farm_uuid}/` | دریافت جزئیات یک مزرعه |
| PATCH | `/api/farm-hub/{farm_uuid}/` | ویرایش مزرعه |
| DELETE | `/api/farm-hub/{farm_uuid}/` | حذف مزرعه |
| POST | `/api/farm-hub/active/` | فعال‌کردن مزرعه |
| POST | `/api/farm-hub/deactive/` | غیرفعال‌کردن مزرعه |

---

## 1) دریافت لیست مزارع

### Request

```http
GET /api/farm-hub/
Authorization: Bearer <token>
```

### رفتار

- فقط مزارع متعلق به کاربر جاری برگردانده می‌شوند.
- برای هر مزرعه، اطلاعات `farm_type`، لیست `products`، لیست `sensors` و `area_uuid` برگردانده می‌شود.

### Response 200

```json
{
  "code": 200,
  "msg": "success",
  "data": [
    {
      "farm_uuid": "550e8400-e29b-41d4-a716-446655440000",
      "area_uuid": "0c7dfd7f-94bf-46f3-b2f9-30a89f0a1111",
      "name": "مزرعه شماره 1",
      "is_active": true,
      "farm_type": {
        "uuid": "11111111-1111-1111-1111-111111111111",
        "name": "زراعی",
        "description": "",
        "metadata": {}
      },
      "products": [
        {
          "uuid": "22222222-2222-2222-2222-222222222222",
          "name": "گندم",
          "description": "",
          "metadata": {},
          "light": "",
          "watering": "",
          "soil": "",
          "temperature": "",
          "planting_season": "پاییز",
          "harvest_time": "بهار",
          "spacing": "",
          "fertilizer": "",
          "health_profile": {
            "moisture": {
              "ideal_value": 65
            }
          },
          "irrigation_profile": {},
          "growth_profile": {}
        }
      ],
      "sensors": [
        {
          "uuid": "33333333-3333-3333-3333-333333333333",
          "sensor_catalog_uuid": "44444444-4444-4444-4444-444444444444",
          "physical_device_uuid": "55555555-5555-5555-5555-555555555555",
          "name": "Station 1",
          "sensor_type": "weather_station",
          "is_active": true,
          "specifications": {
            "model": "FH-1"
          },
          "power_source": {
            "type": "battery"
          },
          "last_updated": "2025-02-18T12:00:00Z"
        }
      ],
      "last_updated": "2025-02-18T12:00:00Z"
    }
  ]
}
```

---

## 2) ساخت مزرعه جدید

### Request

```http
POST /api/farm-hub/
Authorization: Bearer <token>
Content-Type: application/json
```

### Body

```json
{
  "name": "مزرعه شماره 1",
  "is_active": true,
  "farm_type_uuid": "11111111-1111-1111-1111-111111111111",
  "product_uuids": [
    "22222222-2222-2222-2222-222222222222"
  ],
  "sensors": [
    {
      "sensor_catalog_uuid": "44444444-4444-4444-4444-444444444444",
      "physical_device_uuid": "55555555-5555-5555-5555-555555555555",
      "name": "Station 1",
      "sensor_type": "weather_station",
      "is_active": true,
      "specifications": {
        "model": "FH-1"
      },
      "power_source": {
        "type": "battery"
      }
    }
  ],
  "area_geojson": {
    "type": "Feature",
    "properties": {},
    "geometry": {
      "type": "Polygon",
      "coordinates": [
        [
          [51.418934, 35.706815],
          [51.423054, 35.691062],
          [51.384258, 35.689389],
          [51.418934, 35.706815]
        ]
      ]
    }
  }
}
```

### فیلدهای ورودی

| فیلد | نوع | اجباری | توضیح |
|---|---|---|---|
| `name` | string | بله | نام مزرعه |
| `is_active` | boolean | خیر | وضعیت فعال بودن مزرعه؛ پیش‌فرض مدل `true` است |
| `farm_type_uuid` | uuid | بله | UUID نوع مزرعه |
| `product_uuids` | array[uuid] | بله | لیست UUID محصولات؛ خالی بودن مجاز نیست |
| `sensors` | array | خیر | لیست سنسورهای مزرعه |
| `area_geojson` | object | خیر | محدوده زمین به صورت GeoJSON از نوع `Polygon` |

### فیلدهای هر سنسور در `sensors`

| فیلد | نوع | اجباری | توضیح |
|---|---|---|---|
| `sensor_catalog_uuid` | uuid | خیر | اگر ارسال شود باید در `SensorCatalog` وجود داشته باشد |
| `physical_device_uuid` | uuid | خیر | شناسه دستگاه فیزیکی؛ اگر داده نشود مدل خودش مقدار تولید می‌کند |
| `name` | string | وابسته به ورودی | نام سنسور؛ اگر `sensor_catalog_uuid` معتبر باشد و `name` نفرستید، از نام catalog استفاده می‌شود، ولی اگر `sensor_catalog_uuid` هم نداشته باشید عملا باید `name` را بفرستید |
| `sensor_type` | string | خیر | نوع سنسور |
| `is_active` | boolean | خیر | وضعیت فعال بودن سنسور |
| `specifications` | object | خیر | مشخصات فنی |
| `power_source` | object | خیر | نوع یا جزئیات منبع تغذیه |

### اعتبارسنجی‌ها

- `farm_uuid` اگر از سمت کلاینت ارسال شود نادیده گرفته می‌شود.
- `farm_type_uuid` باید معتبر باشد، وگرنه:

```json
{
  "farm_type_uuid": [
    "Farm type not found."
  ]
}
```

- `product_uuids` باید همگی وجود داشته باشند:

```json
{
  "product_uuids": [
    "One or more products were not found."
  ]
}
```

- همه محصولات باید متعلق به همان `farm_type` باشند:

```json
{
  "product_uuids": [
    "Products must belong to farm type `زراعی`."
  ]
}
```

- `sensor_catalog_uuid` اگر ارسال شود باید معتبر باشد:

```json
{
  "sensors": [
    {
      "sensor_catalog_uuid": [
        "Sensor catalog not found."
      ]
    }
  ]
}
```

- `area_geojson` باید object معتبر باشد.
- اگر `area_geojson.type == "Feature"` باشد، مقدار `geometry` بررسی می‌شود.
- `geometry.type` فقط باید `Polygon` باشد.
- `coordinates` باید ساختار polygon ring داشته باشد.

نمونه خطاهای `area_geojson`:

```json
{
  "area_geojson": [
    "`area_geojson` must be a GeoJSON object."
  ]
}
```

```json
{
  "area_geojson": [
    "`area_geojson.geometry.type` must be `Polygon`."
  ]
}
```

### رفتار داخلی مهم

- اگر `area_geojson` ارسال نشود، سیستم از `get_default_area_feature()` استفاده می‌کند.
- بعد از ساخت مزرعه، فرآیند zoning اجرا می‌شود.
- خروجی zoning به `current_crop_area` وصل می‌شود.
- اگر zoning با موفقیت ساخته شود، در response فیلد `zoning` هم برگردانده می‌شود.

### Response 201

```json
{
  "code": 201,
  "msg": "success",
  "data": {
    "farm_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "area_uuid": "0c7dfd7f-94bf-46f3-b2f9-30a89f0a1111",
    "name": "مزرعه شماره 1",
    "is_active": true,
    "farm_type": {
      "uuid": "11111111-1111-1111-1111-111111111111",
      "name": "زراعی",
      "description": "",
      "metadata": {}
    },
    "products": [
      {
        "uuid": "22222222-2222-2222-2222-222222222222",
        "name": "گندم",
        "description": "",
        "metadata": {},
        "light": "",
        "watering": "",
        "soil": "",
        "temperature": "",
        "planting_season": "پاییز",
        "harvest_time": "بهار",
        "spacing": "",
        "fertilizer": "",
        "health_profile": {},
        "irrigation_profile": {},
        "growth_profile": {}
      }
    ],
    "sensors": [
      {
        "uuid": "33333333-3333-3333-3333-333333333333",
        "sensor_catalog_uuid": "44444444-4444-4444-4444-444444444444",
        "physical_device_uuid": "55555555-5555-5555-5555-555555555555",
        "name": "Station 1",
        "sensor_type": "weather_station",
        "is_active": true,
        "specifications": {
          "model": "FH-1"
        },
        "power_source": {
          "type": "battery"
        },
        "last_updated": "2025-02-18T12:00:00Z"
      }
    ],
    "last_updated": "2025-02-18T12:00:00Z",
    "zoning": {
      "zone_count": 4
    }
  }
}
```

### Response 500

در صورتی که سرویس لازم برای zoning/config به‌درستی تنظیم نشده باشد:

```json
{
  "code": 500,
  "msg": "..."
}
```

---

## 3) دریافت لیست نوع مزرعه‌ها

### Request

```http
GET /api/farm-hub/farm-types/
Authorization: Bearer <token>
```

### Response 200

```json
{
  "code": 200,
  "msg": "success",
  "data": [
    {
      "uuid": "11111111-1111-1111-1111-111111111111",
      "name": "زراعی",
      "description": "",
      "metadata": {}
    },
    {
      "uuid": "22222222-2222-2222-2222-222222222222",
      "name": "درختی",
      "description": "",
      "metadata": {}
    }
  ]
}
```

### نکته

- خروجی بر اساس `name` مرتب می‌شود.

---

## 4) دریافت محصولات یک نوع مزرعه

### Request

```http
GET /api/farm-hub/farm-types/{farm_type_uuid}/products/
Authorization: Bearer <token>
```

### Path Params

| پارامتر | نوع | توضیح |
|---|---|---|
| `farm_type_uuid` | uuid | شناسه نوع مزرعه |

### Response 200

```json
{
  "code": 200,
  "msg": "success",
  "data": [
    {
      "uuid": "22222222-2222-2222-2222-222222222222",
      "name": "گندم",
      "description": "",
      "metadata": {},
      "light": "",
      "watering": "",
      "soil": "",
      "temperature": "",
      "planting_season": "پاییز",
      "harvest_time": "بهار",
      "spacing": "",
      "fertilizer": "",
      "health_profile": {
        "moisture": {
          "ideal_value": 65
        }
      },
      "irrigation_profile": {},
      "growth_profile": {}
    }
  ]
}
```

### Response 404

```json
{
  "code": 404,
  "msg": "Farm type not found."
}
```

### نکته

- محصولات با ترتیب `name` برگردانده می‌شوند.

---

## 5) دریافت جزئیات یک مزرعه

### Request

```http
GET /api/farm-hub/{farm_uuid}/
Authorization: Bearer <token>
```

### Path Params

| پارامتر | نوع | توضیح |
|---|---|---|
| `farm_uuid` | uuid | شناسه مزرعه |

### رفتار

- فقط اگر مزرعه متعلق به کاربر جاری باشد برگردانده می‌شود.
- اگر UUID وجود داشته باشد ولی متعلق به کاربر دیگری باشد، عملا مثل not found رفتار می‌شود.

### Response 200

ساختار `data` دقیقا مثل آیتم‌های خروجی لیست مزرعه‌ها است.

### Response 404

```json
{
  "code": 404,
  "msg": "Farm not found."
}
```

---

## 6) ویرایش مزرعه

### Request

```http
PATCH /api/farm-hub/{farm_uuid}/
Authorization: Bearer <token>
Content-Type: application/json
```

### Path Params

| پارامتر | نوع | توضیح |
|---|---|---|
| `farm_uuid` | uuid | شناسه مزرعه |

### Body

این endpoint از `partial update` استفاده می‌کند؛ یعنی می‌توانید فقط بخشی از فیلدها را بفرستید.

نمونه:

```json
{
  "name": "مزرعه اصلاح شده",
  "is_active": false,
  "farm_type_uuid": "11111111-1111-1111-1111-111111111111",
  "product_uuids": [
    "22222222-2222-2222-2222-222222222222"
  ],
  "sensors": [
    {
      "sensor_catalog_uuid": "44444444-4444-4444-4444-444444444444",
      "physical_device_uuid": "55555555-5555-5555-5555-555555555555",
      "name": "Station Updated",
      "sensor_type": "weather_station",
      "is_active": true,
      "specifications": {
        "model": "FH-2"
      },
      "power_source": {
        "type": "solar"
      }
    }
  ]
}
```

### رفتار update

- `name` و `is_active` در صورت ارسال تغییر می‌کنند.
- اگر `farm_type_uuid` ارسال شود، نوع مزرعه به‌روزرسانی می‌شود.
- اگر `product_uuids` ارسال شود، همه محصولات مزرعه با لیست جدید جایگزین می‌شوند.
- اگر `sensors` ارسال شود، همه سنسورهای قبلی حذف و سپس سنسورهای جدید از نو ساخته می‌شوند.
- `area_geojson` در متد `update` دریافت می‌شود ولی در حال حاضر برای update نادیده گرفته می‌شود و zoning مجدد انجام نمی‌شود.

### اعتبارسنجی

همان قوانین create اینجا هم برقرار است، با این تفاوت:

- در update، اگر `farm_type_uuid` ارسال نشود، از `farm_type` فعلی استفاده می‌شود.
- در update، اگر `product_uuids` ارسال نشود، محصولات فعلی حفظ می‌شوند.
- در update، اگر `sensors` ارسال نشود، سنسورهای فعلی حفظ می‌شوند.

### Response 200

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "farm_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "area_uuid": "0c7dfd7f-94bf-46f3-b2f9-30a89f0a1111",
    "name": "مزرعه اصلاح شده",
    "is_active": false,
    "farm_type": {
      "uuid": "11111111-1111-1111-1111-111111111111",
      "name": "زراعی",
      "description": "",
      "metadata": {}
    },
    "products": [],
    "sensors": [],
    "last_updated": "2025-02-18T13:00:00Z"
  }
}
```

### Response 404

```json
{
  "code": 404,
  "msg": "Farm not found."
}
```

---

## 7) حذف مزرعه

### Request

```http
DELETE /api/farm-hub/{farm_uuid}/
Authorization: Bearer <token>
```

### Response 200

```json
{
  "code": 200,
  "msg": "success"
}
```

### Response 404

```json
{
  "code": 404,
  "msg": "Farm not found."
}
```

### نکته

- فقط مزرعه متعلق به کاربر جاری حذف می‌شود.

---

## 8) فعال‌کردن مزرعه

### Request

```http
POST /api/farm-hub/active/
Authorization: Bearer <token>
Content-Type: application/json
```

### Body

```json
{
  "farm_uuid": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Response 200

```json
{
  "code": 200,
  "msg": "success"
}
```

### Response 404

```json
{
  "code": 404,
  "msg": "Farm not found."
}
```

### خطای validation

اگر `farm_uuid` ارسال نشود یا فرمت آن درست نباشد، خطای serializer برگردانده می‌شود. نمونه:

```json
{
  "farm_uuid": [
    "This field is required."
  ]
}
```

---

## 9) غیرفعال‌کردن مزرعه

### Request

```http
POST /api/farm-hub/deactive/
Authorization: Bearer <token>
Content-Type: application/json
```

### Body

```json
{
  "farm_uuid": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Response 200

```json
{
  "code": 200,
  "msg": "success"
}
```

### Response 404

```json
{
  "code": 404,
  "msg": "Farm not found."
}
```

---

## ساختار آبجکت‌ها

## آبجکت `FarmType`

```json
{
  "uuid": "11111111-1111-1111-1111-111111111111",
  "name": "زراعی",
  "description": "",
  "metadata": {}
}
```

## آبجکت `Product`

```json
{
  "uuid": "22222222-2222-2222-2222-222222222222",
  "name": "گندم",
  "description": "",
  "metadata": {},
  "light": "",
  "watering": "",
  "soil": "",
  "temperature": "",
  "planting_season": "",
  "harvest_time": "",
  "spacing": "",
  "fertilizer": "",
  "health_profile": {},
  "irrigation_profile": {},
  "growth_profile": {}
}
```

### توضیح فیلدهای پروفایل محصول

- `health_profile`: برای KPIها و سلامت محصول
- `irrigation_profile`: برای محاسبات آبیاری و ETc
- `growth_profile`: برای مدل رشد مانند GDD

نمونه ساختار `health_profile`:

```json
{
  "moisture": {
    "ideal_value": 65,
    "min_range": 45,
    "max_range": 75,
    "weight": 0.4
  }
}
```

نمونه ساختار `irrigation_profile`:

```json
{
  "kc_initial": 0.6,
  "kc_mid": 1.15,
  "kc_end": 0.8,
  "growth_stage_duration": {
    "initial": 20,
    "mid": 30,
    "late": 25
  }
}
```

نمونه ساختار `growth_profile`:

```json
{
  "base_temperature": 10,
  "required_gdd_for_maturity": 1200,
  "stage_thresholds": {
    "flowering": 500,
    "fruiting": 850
  },
  "current_cumulative_gdd": 320
}
```

## آبجکت `FarmSensor`

```json
{
  "uuid": "33333333-3333-3333-3333-333333333333",
  "sensor_catalog_uuid": "44444444-4444-4444-4444-444444444444",
  "physical_device_uuid": "55555555-5555-5555-5555-555555555555",
  "name": "Station 1",
  "sensor_type": "weather_station",
  "is_active": true,
  "specifications": {},
  "power_source": {},
  "last_updated": "2025-02-18T12:00:00Z"
}
```

## آبجکت `FarmHub`

```json
{
  "farm_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "area_uuid": "0c7dfd7f-94bf-46f3-b2f9-30a89f0a1111",
  "name": "مزرعه شماره 1",
  "is_active": true,
  "farm_type": {},
  "products": [],
  "sensors": [],
  "last_updated": "2025-02-18T12:00:00Z"
}
```

---

## نکات مهم برای فرانت‌اند

- برای ساخت مزرعه، ابتدا `GET /api/farm-hub/farm-types/` را صدا بزنید.
- سپس برای نوع انتخاب‌شده، `GET /api/farm-hub/farm-types/{farm_type_uuid}/products/` را بگیرید.
- برای ساخت یا ویرایش مزرعه، `product_uuids` باید با `farm_type_uuid` هم‌خوانی داشته باشند.
- اگر در update فیلد `sensors` را بفرستید، لیست قبلی کامل جایگزین می‌شود.
- اگر در create، `area_geojson` نفرستید، سیستم خودش یک محدوده پیش‌فرض می‌سازد.
- endpointهای detail/update/delete/active/deactive فقط روی مزرعه‌های خود کاربر عمل می‌کنند.

---

## منبع پیاده‌سازی

- رجیستر اپ: `farm_hub/apps.py`
- تعریف routeها: `farm_hub/urls.py`
- منطق APIها: `farm_hub/views.py`
- serializerها و validation: `farm_hub/serializers.py`
- مدل‌ها: `farm_hub/models.py`
- منطق ساخت zoning: `farm_hub/services.py`
- نمونه requestها: `farm_hub/postman/farm_hub.json`
