# مستند تحویل تغییرات بک‌اند به فرانت

این فایل خلاصه و جمع‌بندی دقیقی از تغییرات انجام‌شده در بک‌اند است تا تیم فرانت بتواند بدون بررسی diffها، مصرف APIها را به‌روزرسانی کند.

---

## جمع‌بندی خیلی کوتاه

بزرگ‌ترین تغییر این release این است که محور اصلی داده‌ها از `sensor` به `farm` منتقل شده است.

یعنی:

- مسیر `sensor-hub` حذف شده و به `farm-hub` تغییر کرده است.
- در endpointهای مختلف، `sensor_uuid` حذف و `farm_uuid` جایگزین شده است.
- چند API که قبلا عمومی یا mock بودند، حالا per-farm و وابسته به مزرعه‌ی انتخاب‌شده هستند.
- بعضی responseها فیلد `farm_uuid` را هم برمی‌گردانند تا state فرانت دقیق‌تر بماند.
- بعضی endpointهایی که در داک قبلی/پست‌من وجود داشتند، الان route فعال ندارند و نباید از سمت فرانت صدا زده شوند.

---

## اقدام لازم برای فرانت

فرانت باید از این به بعد یک `farm_uuid` فعال/انتخاب‌شده در state سراسری داشته باشد و آن را در درخواست‌های مرتبط ارسال کند.

در عمل:

1. بعد از گرفتن لیست مزارع از `GET /api/farm-hub/`، یک مزرعه‌ی active/current انتخاب کنید.
2. `farm_uuid` همان مزرعه را برای dashboard، crop zoning، AI assistant، irrigation recommendation و fertilization recommendation ارسال کنید.
3. هر جایی که قبلا `sensor_uuid` استفاده می‌شد، باید با `farm_uuid` جایگزین شود.

---

## Breaking Changes

### 1) تغییر مسیر اصلی ماژول مزرعه

- قبلی: `/api/sensor-hub/`
- جدید: `/api/farm-hub/`

اگر فرانت هنوز route قبلی را صدا بزند، دیگر کار نخواهد کرد.

---

### 2) حذف `sensor_uuid` از crop zoning

در crop zoning دیگر `sensor_uuid` معتبر نیست.

- قبلی:

```http
GET /api/crop-zoning/area/?sensor_uuid=<uuid>
```

- جدید:

```http
GET /api/crop-zoning/area/?farm_uuid=<uuid>
```

---

### 3) dashboard config و dashboard cards حالا per-farm هستند

این دو endpoint دیگر global نیستند و بدون `farm_uuid` نباید مصرف شوند:

- `GET /api/farm-dashboard-config/?farm_uuid=...`
- `PATCH /api/farm-dashboard-config/`
- `GET /api/farm-dashboard/?farm_uuid=...`

نکته مهم:

- در `GET`، `farm_uuid` باید در query باشد.
- در `PATCH`، `farm_uuid` باید داخل body باشد.

---

### 4) Farm AI Assistant حالا کاملا farm-scoped است

تمام flow چت حالا به مزرعه گره خورده است.

یعنی:

- لیست چت‌ها per-farm است.
- ساخت conversation جدید بدون `farm_uuid` ممکن نیست.
- گرفتن پیام‌ها و حذف conversation هم نیاز به `farm_uuid` دارد.
- responseها در چند endpoint جدیدا `farm_uuid` برمی‌گردانند.

---

### 5) Recommendation APIها بدون `farm_uuid` معتبر نیستند

برای هر دو ماژول:

- `fertilization-recommendation`
- `irrigation-recommendation`

الان `farm_uuid` اجباری شده است:

- در `config` به‌صورت query param
- در `recommend` به‌صورت body
- در `status` به‌صورت query param

---

## نکته مهم درباره routeهای فعال

چند endpoint در کد view وجود دارند یا در داک‌های قدیمی/پست‌من دیده می‌شوند، ولی الان route فعال ندارند. فرانت نباید روی آن‌ها حساب کند.

### routeهای غیرفعال فعلی

- `POST /api/farm-ai-assistant/chat/`
- `GET /api/farm-dashboard/cards/`
- `POST /api/crop-zoning/zones/initial/`
- `POST /api/crop-zoning/zones/water-need/`
- `POST /api/crop-zoning/zones/soil-quality/`
- `POST /api/crop-zoning/zones/cultivation-risk/`

### routeهای فعال فعلی

فقط routeهایی که در این فایل آمده‌اند مبنای فرانت باشند.

---

## 1) Farm Hub

### هدف

ماژول جدید `farm-hub` جایگزین `sensor-hub` شده و موجودیت اصلی فرانت برای انتخاب مزرعه، نمایش سنسورها، ساخت مزرعه و مدیریت فعال/غیرفعال بودن مزرعه است.

### Base Path

```text
/api/farm-hub/
```

### endpointهای فعال

| Method | Path | توضیح |
|---|---|---|
| GET | `/api/farm-hub/` | لیست مزارع کاربر |
| POST | `/api/farm-hub/` | ساخت مزرعه جدید |
| GET | `/api/farm-hub/{farm_uuid}/` | جزئیات مزرعه |
| PATCH | `/api/farm-hub/{farm_uuid}/` | آپدیت مزرعه |
| DELETE | `/api/farm-hub/{farm_uuid}/` | حذف مزرعه |
| POST | `/api/farm-hub/active/` | فعال‌کردن مزرعه |
| POST | `/api/farm-hub/deactive/` | غیرفعال‌کردن مزرعه |

### ساختار response مزرعه

```json
{
  "farm_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "name": "مزرعه نمونه",
  "is_active": true,
  "customization": {},
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
      "metadata": {}
    }
  ],
  "sensors": [
    {
      "uuid": "33333333-3333-3333-3333-333333333333",
      "name": "Station 1",
      "sensor_type": "weather_station",
      "is_active": true,
      "specifications": {},
      "power_source": {},
      "customization": {},
      "last_updated": "2025-02-18T12:00:00Z"
    }
  ],
  "last_updated": "2025-02-18T12:00:00Z"
}
```

### نکات مهم برای فرانت

- شناسه اصلی مزرعه `farm_uuid` است.
- هر مزرعه `farm_type`، `products` و `sensors` را به‌صورت nested برمی‌گرداند.
- سنسورها دیگر top-level resource مستقل برای UI نیستند؛ داخل خود مزرعه برمی‌گردند.
- endpoint جداگانه‌ای برای catalog نوع مزرعه/محصول در این diff اضافه نشده است.

### ساخت مزرعه

نمونه body:

```json
{
  "name": "farm-1",
  "farm_type_uuid": "11111111-1111-1111-1111-111111111111",
  "product_uuids": [
    "22222222-2222-2222-2222-222222222222"
  ],
  "customization": {
    "report_interval_sec": 300
  },
  "sensors": [
    {
      "name": "Station 1",
      "sensor_type": "weather_station",
      "is_active": true,
      "specifications": {
        "model": "FH-1"
      },
      "power_source": {
        "type": "battery"
      },
      "customization": {
        "report_interval_sec": 300
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

### تغییر مهم در create farm

اگر `area_geojson` ارسال شود:

- مزرعه ساخته می‌شود
- zoning اولیه هم برای همان مزرعه ساخته می‌شود
- در response، فیلد `zoning` هم برمی‌گردد

این برای فرانت خیلی مهم است چون بعد از ساخت مزرعه می‌تواند مستقیم zoning اولیه را برای map استفاده کند و لازم نیست منتظر call جداگانه باشد.

### فعال/غیرفعال کردن مزرعه

body هر دو endpoint:

```json
{
  "farm_uuid": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## 2) Crop Zoning

### Base Path

```text
/api/crop-zoning/
```

### endpointهای فعال

| Method | Path | توضیح |
|---|---|---|
| GET | `/api/crop-zoning/area/?farm_uuid=...&page=1&page_size=10` | گرفتن area + task status + zones |
| GET | `/api/crop-zoning/products/` | گرفتن لیست محصولات قابل کشت |
| GET | `/api/crop-zoning/zones/{zone_id}/details/` | جزئیات یک زون |

### breaking change

فقط `farm_uuid` معتبر است و request باید روی مزرعه‌ی متعلق به همان کاربر انجام شود.

### نمونه request

```http
GET /api/crop-zoning/area/?farm_uuid=<farm_uuid>&page=1&page_size=10
```

### نمونه response

```json
{
  "status": "success",
  "data": {
    "task": {
      "status": "SUCCESS",
      "stage": "completed",
      "stage_label": "پردازش همه زون‌ها کامل شده است",
      "area_uuid": "c0eaa4d7-92bf-4542-a60d-6010b45e7c96",
      "total_zones": 364,
      "completed_zones": 364,
      "processing_zones": 0,
      "pending_zones": 0,
      "failed_zones": 0,
      "remaining_zones": 0,
      "progress_percent": 100,
      "summary": {
        "done": 364,
        "in_progress": 0,
        "remaining": 0,
        "failed": 0
      },
      "message": "از مجموع 364 زون، 364 زون پردازش شده، 0 زون در حال پردازش و 0 زون باقی مانده است.",
      "failed_zone_errors": [],
      "cell_side_km": 0.1
    },
    "area": {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": []
      },
      "properties": {
        "center": {
          "latitude": 35.69575533,
          "longitude": 51.40874867
        },
        "area_sqm": 3109868.97,
        "cell_side_km": 0.1,
        "area_hectares": 310.9869
      }
    },
    "zones": [],
    "pagination": {
      "page": 1,
      "page_size": 10,
      "total_pages": 37,
      "total_zones": 364,
      "returned_zones": 10,
      "has_next": true,
      "has_previous": false
    }
  }
}
```

### نکات مهم برای فرانت

- `zones` صفحه‌بندی‌شده است؛ کل زون‌ها در هر response برنمی‌گردند.
- فرانت باید با `task.status` و `task.stage` polling را مدیریت کند.
- `page` و `page_size` هنوز اختیاری هستند.
- اگر مزرعه area نداشته باشد، بک‌اند خودش area/zones را برای همان مزرعه ایجاد می‌کند.

### خطاها

#### نبودن `farm_uuid`

```json
{
  "status": "error",
  "message": "farm_uuid is required."
}
```

#### پیدا نشدن مزرعه

```json
{
  "status": "error",
  "message": "Farm not found."
}
```

---

## 3) Farm Dashboard

### Base Path

```text
/api/farm-dashboard/
```

### Config Path

```text
/api/farm-dashboard-config/
```

### تغییر اصلی

dashboard config دیگر mock/global نیست و برای هر مزرعه جداگانه در دیتابیس ذخیره می‌شود.

### endpointهای فعال

| Method | Path | توضیح |
|---|---|---|
| GET | `/api/farm-dashboard-config/?farm_uuid=...` | گرفتن تنظیمات داشبورد همان مزرعه |
| PATCH | `/api/farm-dashboard-config/` | آپدیت partial تنظیمات داشبورد همان مزرعه |
| GET | `/api/farm-dashboard/?farm_uuid=...` | گرفتن داده کارت‌های داشبورد برای همان مزرعه |

### نکات مهم برای فرانت

- `GET /api/farm-dashboard/cards/` الان route فعال ندارد؛ فقط base path فعال است.
- در response config، فیلد `farm_uuid` اضافه شده است.
- در `PATCH` حتی اگر فقط یک فیلد را تغییر می‌دهید، باز هم باید `farm_uuid` را بفرستید.

### GET config

```http
GET /api/farm-dashboard-config/?farm_uuid=<farm_uuid>
```

### GET config response

```json
{
  "code": 200,
  "msg": "OK",
  "data": {
    "farm_uuid": "550e8400-e29b-41d4-a716-446655440000",
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

### PATCH config sample

```json
{
  "farm_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "disabled_card_ids": [
    "farmWeatherCard"
  ]
}
```

### rule مهم PATCH

اگر body فقط این باشد:

```json
{
  "farm_uuid": "..."
}
```

خطای validation می‌گیرید، چون باید حداقل یکی از این‌ها هم باشد:

- `disabled_card_ids`
- `row_order`
- `enable_drag_reorder`

### خطاهای متداول

#### نبودن `farm_uuid`

```json
{
  "farm_uuid": [
    "This field is required."
  ]
}
```

#### مزرعه متعلق به کاربر نباشد

```json
{
  "farm_uuid": [
    "Farm not found."
  ]
}
```

---

## 4) Farm AI Assistant

### Base Path

```text
/api/farm-ai-assistant/
```

### endpointهای فعال

| Method | Path | توضیح |
|---|---|---|
| GET | `/api/farm-ai-assistant/context/?farm_uuid=...` | گرفتن context مزرعه برای نوار/summary |
| GET | `/api/farm-ai-assistant/chats/?farm_uuid=...` | لیست conversationهای همان مزرعه |
| POST | `/api/farm-ai-assistant/chats/` | ساخت conversation جدید |
| GET | `/api/farm-ai-assistant/chats/{conversation_id}/messages/?farm_uuid=...` | گرفتن پیام‌ها |
| DELETE | `/api/farm-ai-assistant/chats/{conversation_id}/?farm_uuid=...` | حذف conversation |
| POST | `/api/farm-ai-assistant/chat/task/` | ایجاد task چت |
| GET | `/api/farm-ai-assistant/chat/task/{task_id}/status/?farm_uuid=...` | گرفتن وضعیت task |

### نکته خیلی مهم

`POST /api/farm-ai-assistant/chat/` الان route فعال ندارد.

پس flow فعلی فرانت باید async باشد:

1. `POST /chat/task/`
2. polling روی `GET /chat/task/{task_id}/status/`

### تغییرات مهم response

فیلد `farm_uuid` در این قسمت‌ها اضافه شده است:

- conversation summary
- لیست پیام‌ها
- delete response
- task create response
- task status response
- assistant payload نهایی

### GET context

```http
GET /api/farm-ai-assistant/context/?farm_uuid=<farm_uuid>
```

نمونه response:

```json
{
  "status": "success",
  "data": {
    "farm_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "soilType": "Loamy",
    "waterEC": "1.2 dS/m",
    "selectedCrop": "Tomato",
    "growthStage": "Flowering",
    "lastIrrigationStatus": "2 days ago"
  }
}
```

### GET chats response

```json
{
  "status": "success",
  "data": [
    {
      "id": "conv-123",
      "farm_uuid": "550e8400-e29b-41d4-a716-446655440000",
      "message_count": 4
    }
  ]
}
```

### POST chats request

```json
{
  "farm_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "title": "New chat",
  "farm_context": {
    "soilType": "Loamy"
  }
}
```

### POST chat task request

```json
{
  "farm_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "conversation_id": "7a26d99a-8d67-467d-a4a8-4c46b62b6bc2",
  "content": "What is the best irrigation plan?",
  "images": [],
  "farm_context": {
    "soilType": "Loamy"
  }
}
```

### POST chat task response

```json
{
  "status": "success",
  "data": {
    "task_id": "farm-ai-chat-task-123",
    "status": "PENDING",
    "status_url": "/api/tasks/farm-ai-chat-task-123/status/",
    "conversation_id": "7a26d99a-8d67-467d-a4a8-4c46b62b6bc2",
    "message_id": "2cbd4d61-363d-4f7c-a46a-a78cf28f6dd8",
    "farm_uuid": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### GET task status response در حالت success

```json
{
  "status": "success",
  "data": {
    "task_id": "farm-ai-chat-task-123",
    "status": "SUCCESS",
    "conversation_id": "7a26d99a-8d67-467d-a4a8-4c46b62b6bc2",
    "farm_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "result": {
      "message_id": "msg-001",
      "conversation_id": "7a26d99a-8d67-467d-a4a8-4c46b62b6bc2",
      "farm_uuid": "550e8400-e29b-41d4-a716-446655440000",
      "content": "Here is the recommended plan.",
      "sections": []
    }
  }
}
```

### نکات مهم برای فرانت

- conversationها حالا per-farm هستند؛ لیست چت مزرعه A لزوما برای مزرعه B مشترک نیست.
- برای گرفتن messages و delete هم باید `farm_uuid` در query بفرستید.
- در response پیام‌ها، هم top-level و هم هر message شامل `farm_uuid` است.

### خطاها

- اگر `farm_uuid` نفرستید: `400`
- اگر مزرعه پیدا نشود: در این ماژول معمولا `404`

---

## 5) Fertilization Recommendation

### Base Path

```text
/api/fertilization-recommendation/
```

### endpointهای فعال

| Method | Path | توضیح |
|---|---|---|
| GET | `/api/fertilization-recommendation/config/?farm_uuid=...` | گرفتن داده اولیه فرم |
| POST | `/api/fertilization-recommendation/recommend/` | ساخت recommendation |
| GET | `/api/fertilization-recommendation/recommend/status/{task_id}/?farm_uuid=...` | وضعیت task |

### breaking change

`farm_uuid` برای این ماژول اجباری شده است.

### GET config

```http
GET /api/fertilization-recommendation/config/?farm_uuid=<farm_uuid>
```

### response config

```json
{
  "status": "success",
  "data": {
    "farm_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "farmData": {
      "soilType": "Loamy",
      "organicMatter": "Medium (2.5%)",
      "waterEC": "1.2 dS/m"
    },
    "growthStages": [],
    "cropOptions": []
  }
}
```

### POST recommend request

```json
{
  "farm_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "crop_id": "wheat",
  "growth_stage": "flowering",
  "farm_data": {
    "soilType": "Loamy",
    "organicMatter": "Medium (2.5%)",
    "waterEC": "1.2 dS/m"
  }
}
```

### نکات مهم برای فرانت

- اگر `farm_uuid` نفرستید، validation error می‌گیرید.
- در status endpoint هم `farm_uuid` باید query param باشد.
- بک‌اند درخواست/پاسخ recommendation را برای هر مزرعه ذخیره می‌کند، ولی این persistence فعلا response shape فرانت را تغییر نمی‌دهد.

### نمونه خطا

```json
{
  "code": 400,
  "msg": "داده نامعتبر.",
  "data": {
    "farm_uuid": [
      "This field is required."
    ]
  }
}
```

---

## 6) Irrigation Recommendation

### Base Path

```text
/api/irrigation-recommendation/
```

### endpointهای فعال

| Method | Path | توضیح |
|---|---|---|
| GET | `/api/irrigation-recommendation/config/?farm_uuid=...` | گرفتن داده اولیه فرم |
| POST | `/api/irrigation-recommendation/recommend/` | ساخت recommendation |
| GET | `/api/irrigation-recommendation/recommend/status/{task_id}/?farm_uuid=...` | وضعیت task |

### breaking change

`farm_uuid` برای این ماژول هم اجباری شده است.

### GET config

```http
GET /api/irrigation-recommendation/config/?farm_uuid=<farm_uuid>
```

### response config

```json
{
  "status": "success",
  "data": {
    "farm_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "farmInfo": {
      "soilType": "Loamy",
      "waterQuality": "Medium EC",
      "climateZone": "Temperate"
    },
    "cropOptions": []
  }
}
```

### POST recommend request

```json
{
  "farm_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "crop_id": "wheat",
  "farm_data": {
    "soilType": "Loamy",
    "waterQuality": "Medium EC",
    "climateZone": "Temperate"
  }
}
```

### نکات مهم برای فرانت

- route جداگانه‌ای برای `task create` در urls فعال نیست؛ همان `POST /recommend/` را استفاده کنید.
- برای status هم حتما `farm_uuid` را در query بفرستید.
- response نهایی ممکن است شامل `plan`، `water_balance`، `raw_response` و `status` باشد.

### نمونه خطا

```json
{
  "code": 400,
  "msg": "داده نامعتبر.",
  "data": {
    "farm_uuid": [
      "This field is required."
    ]
  }
}
```

---

## الگوی مشترک خطاها

بسته به ماژول، شکل خطا یکسان نیست. فرانت بهتر است هر دو الگوی زیر را پشتیبانی کند:

### الگوی 1

```json
{
  "status": "error",
  "message": "Farm not found."
}
```

### الگوی 2

```json
{
  "farm_uuid": [
    "Farm not found."
  ]
}
```

### الگوی 3

```json
{
  "detail": "Farm not found"
}
```

پس بهتر است parsing خطا فقط روی یک shape ثابت بسته نشود.

---

## وضعیت احراز هویت

برای endpointهای این فایل، فرانت بهتر است همیشه این هدرها را بفرستد:

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

به‌خصوص در این ماژول‌ها:

- `farm-hub`
- `farm-dashboard`
- `farm-ai-assistant`
- `crop-zoning`
- `fertilization-recommendation`
- `irrigation-recommendation`

---

## چک‌لیست تغییرات لازم در فرانت

### اجباری

- همه referenceهای `sensor_uuid` را به `farm_uuid` تغییر دهید.
- همه callهای `sensor-hub` را به `farm-hub` تغییر دهید.
- یک state مرکزی برای `selectedFarm` یا `currentFarm` داشته باشید.
- قبل از callهای dashboard/zoning/assistant/recommendation، `farm_uuid` مزرعه انتخابی را inject کنید.
- flow چت را از sync به async task-based تغییر دهید.

### مهم

- `GET /api/farm-dashboard/cards/` را با `GET /api/farm-dashboard/?farm_uuid=...` جایگزین کنید.
- در dashboard config patch، `farm_uuid` را داخل body بفرستید.
- اگر روی routeهای crop zoning قدیمی مثل `zones/water-need` حساب کرده‌اید، آن‌ها را از flow حذف کنید.

### بهتر است

- هندل خطا را tolerant بنویسید چون shape خطا بین ماژول‌ها یکسان نیست.
- `farm_uuid` برگشتی responseها را با state فرانت sync نگه دارید.
- بعد از create farm اگر response شامل `zoning` بود، مستقیم آن را برای map استفاده کنید.

---

## جمع‌بندی نهایی

اگر بخواهیم خیلی عملی بگوییم، فرانت برای این release فقط باید این سه اصل را رعایت کند:

1. همه چیز را بر اساس `farm_uuid` مصرف کند، نه `sensor_uuid`.
2. تمام ماژول‌های اصلی را روی مزرعه‌ی انتخابی کاربر scope کند.
3. فقط routeهای فعال فعلی را مصرف کند، نه routeهایی که در داک‌های قدیمی یا پست‌من قبلی دیده می‌شوند.

اگر لازم باشد، مرحله بعدی می‌تواند تولید یک نسخه‌ی کوتاه‌تر مخصوص frontend devها باشد که فقط شامل endpoint matrix و نمونه request/response باشد.
