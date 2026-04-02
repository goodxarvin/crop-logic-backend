# Crop Zoning API Guide For Frontend

این فایل برای تیم فرانت نوشته شده و رفتار endpointهای ماژول `crop-zoning` را به صورت کاربردی توضیح می‌دهد.

## Base Path

```text
/api/crop-zoning/
```

## Authentication

- همه endpointها با تنظیم فعلی پروژه نیاز به احراز هویت دارند.
- هدر پیشنهادی:

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

## Flow پیشنهادی فرانت

1. ابتدا `GET /area/` را با `farm_uuid` صدا بزنید.
2. اگر `task.status` برابر `PENDING` یا `PROCESSING` بود، polling انجام دهید.
3. وقتی `task.status` برابر `SUCCESS` شد:
   - `area` را برای polygon اصلی زمین استفاده کنید.
   - `zones` را برای grid map و کارت‌های overview استفاده کنید.
4. برای legend محصولات، `GET /products/` را بزنید.

## وضعیت‌های Task

- `IDLE`: هنوز area/taskی برای مزرعه وجود ندارد.
- `PENDING`: تسک ساخته شده ولی پردازش هنوز شروع نشده یا در صف است.
- `PROCESSING`: بخشی از زون‌ها در حال پردازش هستند یا برخی کامل شده‌اند.
- `SUCCESS`: همه زون‌ها کامل پردازش شده‌اند.
- `FAILURE`: یک یا چند زون با خطا مواجه شده‌اند.

## Stageهای Task

- `waiting_to_start`
- `queued`
- `processing_zones`
- `continuing_processing`
- `completed`
- `failed`

فیلد `stage_label` متن فارسی آماده برای نمایش در UI است.

---

## 1) Get Area

```http
GET /api/crop-zoning/area/?farm_uuid=<farm_uuid>&page=1&page_size=10
```

### Query Params

- `farm_uuid`: اجباری، UUID مزرعه
- `page`: اختیاری، شماره صفحه زون‌ها. پیش‌فرض `1`
- `page_size`: اختیاری، تعداد زون در هر صفحه. پیش‌فرض `10`

### کاربرد

- گرفتن آخرین area مربوط به مزرعه
- ساخت area و zoneها در صورت نبود داده
- دریافت وضعیت task
- دریافت لیست `zones` به صورت صفحه‌بندی‌شده برای نمایش روی نقشه
- دریافت اطلاعات pagination برای ساخت pager یا infinite loading در فرانت

### نمونه پاسخ موفق

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
        "coordinates": [[[51.418934, 35.706815], [51.423054, 35.691062], [51.384258, 35.689389], [51.418934, 35.706815]]]
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
    "zones": [
      {
        "zoneId": "zone-0",
        "zoneUuid": "d7a9a19b-b3ec-4721-b514-9aae5c9ea940",
        "geometry": {
          "type": "Polygon",
          "coordinates": [[[51.384258, 35.689389], [51.38536404, 35.689389], [51.38536404, 35.69028731], [51.384258, 35.69028731], [51.384258, 35.689389]]]
        },
        "center": {
          "latitude": 35.68983816,
          "longitude": 51.38481102
        },
        "area_sqm": 9999.91,
        "area_hectares": 1,
        "sequence": 0,
        "processing_status": "completed",
        "processing_error": "",
        "crop": "wheat",
        "matchPercent": 89,
        "waterNeed": "4820-5820 m³/ha",
        "estimatedProfit": "۱۵-۲۵ میلیون/هکتار",
        "waterNeedLayer": {
          "level": "medium",
          "value": "4820-5820 m³/ha",
          "color": "#0ea5e9"
        },
        "soilQualityLayer": {
          "level": "high",
          "score": 89,
          "color": "#22c55e"
        },
        "cultivationRiskLayer": {
          "level": "low",
          "color": "#22c55e"
        }
      }
    ],
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

### رفتار pagination

- `zones` فقط شامل زون‌های همان صفحه‌ای است که در query param فرستاده شده
- `task.total_zones` تعداد کل زون‌های area را نشان می‌دهد، نه فقط زون‌های همان صفحه
- `pagination.total_pages` تعداد کل صفحه‌ها را برای فرانت مشخص می‌کند
- `pagination.returned_zones` تعداد آیتم‌های برگشتی در همان response را نشان می‌دهد
- اگر `page` بزرگ‌تر از `total_pages` باشد، response خطا نمی‌دهد و فقط `zones` خالی برمی‌گردد

### مثال‌ها

#### صفحه اول با 10 زون در هر صفحه

```http
GET /api/crop-zoning/area/?farm_uuid=<farm_uuid>&page=1&page_size=10
```

#### صفحه سوم با 25 زون در هر صفحه

```http
GET /api/crop-zoning/area/?farm_uuid=<farm_uuid>&page=3&page_size=25
```

### فیلدهای مهم `zones`

- `zoneId`: شناسه نمایشی زون، مثل `zone-0`
- `zoneUuid`: UUID داخلی زون
- `geometry`: polygon زون
- `center`: مرکز زون
- `area_sqm`: مساحت به متر مربع
- `area_hectares`: مساحت به هکتار
- `sequence`: ترتیب زون
- `processing_status`: یکی از `pending`, `processing`, `completed`, `failed`
- `processing_error`: متن خطا در صورت failure
- `crop`: محصول پیشنهادی
- `matchPercent`: درصد تطابق
- `waterNeed`: نیاز آبی پیشنهادی
- `estimatedProfit`: سود تخمینی
- `waterNeedLayer`: داده layer نیاز آبی
- `soilQualityLayer`: داده layer کیفیت خاک
- `cultivationRiskLayer`: داده layer ریسک کشت

### فیلدهای مهم `pagination`

- `page`: شماره صفحه فعلی
- `page_size`: تعداد زون در هر صفحه
- `total_pages`: تعداد کل صفحه‌ها
- `total_zones`: تعداد کل زون‌های area
- `returned_zones`: تعداد زون‌های برگشتی در response فعلی
- `has_next`: آیا صفحه بعدی وجود دارد یا نه
- `has_previous`: آیا صفحه قبلی وجود دارد یا نه

### خطاها

#### وقتی `farm_uuid` ارسال نشود

```json
{
  "status": "error",
  "message": "farm_uuid is required."
}
```

#### وقتی مزرعه پیدا نشود

```json
{
  "status": "error",
  "message": "Farm not found."
}
```

#### وقتی `page` یا `page_size` نامعتبر باشد

```json
{
  "status": "error",
  "message": "page must be a positive integer."
}
```

- همین رفتار برای `page_size` هم وجود دارد و پیام خطا به صورت
  `page_size must be a positive integer.` برمی‌گردد.

---

## 2) Get Products

```http
GET /api/crop-zoning/products/
```

### کاربرد

- گرفتن لیست محصولات برای legend و labelها

### نمونه پاسخ

```json
{
  "status": "success",
  "data": {
    "products": [
      {
        "id": "wheat",
        "label": "گندم",
        "color": "#6bcb77"
      },
      {
        "id": "canola",
        "label": "کلزا",
        "color": "#ffd93d"
      },
      {
        "id": "saffron",
        "label": "زعفران",
        "color": "#9b59b6"
      }
    ]
  }
}
```
