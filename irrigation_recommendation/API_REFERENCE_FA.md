# مستند API آبیاری و محصولات انتخاب‌شده

این فایل برای تحویل به فرانت نوشته شده و endpointهای مرتبط با آبیاری را به‌صورت کامل توضیح می‌دهد.

محدوده این مستند:
- همه endpointهای `irrigation_recommendation/urls.py`
- endpoint دریافت محصولات انتخاب‌شده مزرعه: `GET /api/plants/selected/`

## نکات عمومی

- همه endpointها نیاز به authentication کاربر دارند، مگر اینکه در gateway یا لایه بالاتر خلاف آن تنظیم شده باشد.
- در همه endpointهای وابسته به مزرعه، `farm_uuid` باید متعلق به همان کاربر لاگین‌شده باشد.
- فرمت کلی پاسخ‌های موفق در این backend معمولاً به شکل زیر است:

```json
{
  "code": 200,
  "msg": "success",
  "data": {}
}
```

- در خطاهای اعتبارسنجی معمولاً ساختار زیر برمی‌گردد:

```json
{
  "farm_uuid": [
    "This field is required."
  ]
}
```

یا در بعضی endpointها:

```json
{
  "code": 404,
  "msg": "error",
  "data": {
    "farm_uuid": [
      "Farm not found."
    ]
  }
}
```

---

# 1) محصولات انتخاب‌شده مزرعه

## GET `/api/plants/selected/`

این endpoint برای گرفتن محصول/محصولات انتخاب‌شده یک مزرعه استفاده می‌شود؛ یعنی همان محصولاتی که روی خود `FarmHub.products` ذخیره شده‌اند.

این endpoint برای فرانت مفید است وقتی می‌خواهید:
- محصول فعلی مزرعه را نمایش دهید
- لیست گیاه‌های متصل به مزرعه را برای انتخاب stage یا recommendation استفاده کنید
- قبل از درخواست recommendation، محصول‌های مرتبط با همان مزرعه را بخوانید

### Query Params

#### `farm_uuid`
- نوع: `string (uuid)`
- اجباری: بله
- توضیح: شناسه مزرعه برای خواندن محصولات انتخاب‌شده آن.

### نمونه درخواست

```bash
curl -s "http://localhost:8000/api/plants/selected/?farm_uuid=11111111-1111-1111-1111-111111111111" \
  -H "accept: application/json" \
  -H "Authorization: Bearer <token>"
```

### پاسخ موفق

```json
{
  "code": 200,
  "msg": "success",
  "data": [
    {
      "name": "گوجه فرنگی",
      "icon": "tabler-carrot",
      "growth_stages": ["رویشی", "گلدهی", "میوه دهی"]
    }
  ]
}
```

### فیلدهای هر آیتم

#### `name`
- نوع: `string`
- توضیح: نام محصول.

#### `icon`
- نوع: `string`
- توضیح: آیکون پیشنهادی برای UI.

#### `growth_stages`
- نوع: `array<string>`
- توضیح: مراحل رشد قابل استفاده برای فرانت.

### خطاهای رایج

#### اگر `farm_uuid` ارسال نشود
```json
{
  "farm_uuid": ["This field is required."]
}
```

#### اگر مزرعه متعلق به کاربر نباشد یا پیدا نشود
```json
{
  "farm_uuid": ["Farm not found."]
}
```

# 5) تولید recommendation آبیاری

## POST `/api/irrigation/recommend/`

این endpoint recommendation آبیاری را تولید می‌کند و خروجی آن با UI فعلی recommendation هماهنگ شده است.

نکته مهم:
- روش آبیاری از body فرانت خوانده نمی‌شود.
- backend روش آبیاری را از خود مزرعه (`FarmHub.irrigation_method_id` و `FarmHub.irrigation_method_name`) برمی‌دارد.
- بنابراین قبل از صدا زدن این endpoint، فرانت باید روش آبیاری انتخاب‌شده را روی مزرعه ذخیره کرده باشد.

## ساختار کلی پاسخ

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "recommendation_uuid": "...",
    "crop_id": "گوجه فرنگی",
    "plant_name": "گوجه فرنگی",
    "growth_stage": "گلدهی",
    "irrigation_method_name": "آبیاری قطره ای",
    "status": "pending_confirmation",
    "status_label": "منتظر تایید",
    "plan": {},
    "water_balance": {},
    "timeline": [],
    "sections": []
  }
}
```

## Request

### حداقل payload پیشنهادی

```json
{
  "farm_uuid": "11111111-1111-1111-1111-111111111111",
  "plant_name": "گوجه فرنگی",
  "growth_stage": "گلدهی"
}
```

### فیلدهای Request

### `farm_uuid`
- نوع: `string`
- اجباری: بله
- توضیح: شناسه یکتای مزرعه.

### `sensor_uuid`
- نوع: `string`
- اجباری: خیر
- توضیح: نام قدیمی برای `farm_uuid`. اگر `farm_uuid` ارسال نشده باشد، این مقدار به جای آن استفاده می‌شود.

### `plant_name`
- نوع: `string`
- اجباری: خیر
- توضیح: نام گیاه هدف برای تولید recommendation.

### `growth_stage`
- نوع: `string`
- اجباری: خیر
- توضیح: مرحله رشد گیاه، مثل `رویشی`، `گلدهی` یا `میوه دهی`.

## فیلدهای `data`

### `recommendation_uuid`
- نوع: `string (uuid)`
- توضیح: شناسه recommendation ذخیره‌شده برای history/detail.

### `crop_id`
- نوع: `string`
- توضیح: نام/شناسه گیاه ذخیره‌شده روی recommendation.

### `plant_name`
- نوع: `string`
- توضیح: معادل `crop_id` برای مصرف آسان‌تر در UI.

### `growth_stage`
- نوع: `string`
- توضیح: مرحله رشد ذخیره‌شده همراه recommendation.

### `irrigation_method_name`
- نوع: `string`
- توضیح: نام روش آبیاری خوانده‌شده از مزرعه.

### `status`
- نوع: `string`
- توضیح: وضعیت recommendation. مقادیر فعلی:
  - `in_progress`
  - `pending_confirmation`
  - `completed`
  - `error`

### `status_label`
- نوع: `string`
- توضیح: متن فارسی وضعیت برای نمایش مستقیم در UI.

### `plan`
- نوع: `object`
- توضیح: خلاصه اصلی recommendation برای کارت بالای UI.

### `water_balance`
- نوع: `object`
- توضیح: تراز آب و خروجی محاسبات روزانه.

### `timeline`
- نوع: `array`
- توضیح: مراحل اجرایی recommendation برای stepper.

### `sections`
- نوع: `array`
- توضیح: هشدارها و نکات تکمیلی.

## نمونه پاسخ حداقلی قابل استفاده

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "recommendation_uuid": "8a4c22d8-3f75-4aef-8e04-b40f6b4a2d11",
    "crop_id": "گوجه فرنگی",
    "plant_name": "گوجه فرنگی",
    "growth_stage": "گلدهی",
    "irrigation_method_name": "آبیاری قطره ای",
    "status": "pending_confirmation",
    "status_label": "منتظر تایید",
    "plan": {
      "frequencyPerWeek": 4,
      "durationMinutes": 38,
      "bestTimeOfDay": "05:30 تا 08:00 صبح",
      "moistureLevel": 72,
      "warning": "در ساعات گرم روز آبیاری انجام نشود"
    },
    "water_balance": {
      "active_kc": 0.93,
      "crop_profile": {
        "kc_initial": 0.55,
        "kc_mid": 1.05,
        "kc_end": 0.78
      },
      "daily": [
        {
          "forecast_date": "2025-02-12",
          "et0_mm": 5.4,
          "etc_mm": 4.9,
          "effective_rainfall_mm": 0,
          "gross_irrigation_mm": 17,
          "irrigation_timing": "05:30 - 07:00"
        }
      ]
    },
    "timeline": [
      {
        "step_number": 1,
        "title": "بررسی فشار",
        "description": "فشار ابتدا و انتهای لاین کنترل شود"
      }
    ],
    "sections": [
      {
        "title": "هشدار تبخیر بالا",
        "icon": "tabler-alert-triangle",
        "type": "warning",
        "content": "در ساعات گرم روز آبیاری انجام نشود"
      },
      {
        "title": "نکته بهره وری",
        "icon": "tabler-bulb",
        "type": "tip",
        "content": "شست وشوی فیلترها به یکنواختی آبیاری کمک می کند"
      }
    ]
  }
}
```

---

# 6) لیست recommendationهای آبیاری

## GET `/api/irrigation/recommendations/`

این endpoint history recommendationهای آبیاری یک مزرعه را برمی‌گرداند.

### Query Params

#### `farm_uuid`
- نوع: `string (uuid)`
- اجباری: بله

#### `page`
- نوع: `number`
- اجباری: خیر
- پیش‌فرض: `1`

#### `page_size`
- نوع: `number`
- اجباری: خیر
- پیش‌فرض backend: `10`
- حداکثر: `100`

### نمونه درخواست

```bash
curl -s "http://localhost:8000/api/irrigation/recommendations/?farm_uuid=11111111-1111-1111-1111-111111111111&page=1&page_size=10" \
  -H "accept: application/json" \
  -H "Authorization: Bearer <token>"
```

### پاسخ موفق نمونه

```json
{
  "code": 200,
  "msg": "success",
  "data": [
    {
      "recommendation_uuid": "8a4c22d8-3f75-4aef-8e04-b40f6b4a2d11",
      "crop_id": "گوجه فرنگی",
      "plant_name": "گوجه فرنگی",
      "growth_stage": "گلدهی",
      "irrigation_method_name": "آبیاری قطره ای",
      "status": "pending_confirmation",
      "status_label": "منتظر تایید",
      "requested_at": "2025-02-12T09:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_pages": 1,
    "total_items": 1,
    "has_next": false,
    "has_previous": false,
    "next": null,
    "previous": null
  }
}
```

### فیلدهای هر آیتم

#### `recommendation_uuid`
- نوع: `string (uuid)`
- توضیح: شناسه recommendation برای باز کردن جزئیات.

#### `crop_id`
- نوع: `string`
- توضیح: نام/شناسه گیاه.

#### `plant_name`
- نوع: `string`
- توضیح: معادل `crop_id`.

#### `growth_stage`
- نوع: `string`
- توضیح: مرحله رشد ثبت‌شده.

#### `irrigation_method_name`
- نوع: `string`
- توضیح: نام روش آبیاری.

#### `status`
- نوع: `string`
- توضیح: وضعیت recommendation.

#### `status_label`
- نوع: `string`
- توضیح: متن فارسی وضعیت.

#### `requested_at`
- نوع: `string(datetime)`
- توضیح: زمان ساخت recommendation.

---

# 7) جزئیات یک recommendation آبیاری

## GET `/api/irrigation/recommendations/{recommendation_uuid}/`

این endpoint جزئیات یک recommendation ذخیره‌شده را با همان shape endpoint اصلی recommendation برمی‌گرداند.

### Path Params

#### `recommendation_uuid`
- نوع: `string (uuid)`
- اجباری: بله
- توضیح: شناسه recommendation.

### پاسخ موفق نمونه

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "recommendation_uuid": "8a4c22d8-3f75-4aef-8e04-b40f6b4a2d11",
    "crop_id": "گوجه فرنگی",
    "plant_name": "گوجه فرنگی",
    "growth_stage": "گلدهی",
    "irrigation_method_name": "آبیاری قطره ای",
    "status": "completed",
    "status_label": "پایان یافته",
    "plan": {
      "frequencyPerWeek": 4,
      "durationMinutes": 30
    },
    "water_balance": {
      "active_kc": 0.93,
      "daily": []
    },
    "timeline": [
      {
        "step_number": 1,
        "title": "مرحله اول",
        "description": "اجرا شود"
      }
    ],
    "sections": [
      {
        "type": "tip",
        "title": "نکته",
        "content": "صبح زود آبیاری شود"
      }
    ]
  }
}
```

### خطای عدم وجود recommendation

```json
{
  "code": 404,
  "msg": "Recommendation not found."
}
```

---


# 9) پیشنهاد جریان استفاده در فرانت

برای صفحه recommendation آبیاری، ترتیب پیشنهادی این است:

1. با `GET /api/irrigation/` لیست روش‌های آبیاری را بگیرید.
2. کاربر یکی از روش‌ها را انتخاب کند.
3. روش انتخاب‌شده را روی مزرعه ذخیره کنید (`irrigation_method_id` و `irrigation_method_name`).
4. با `GET /api/plants/selected/?farm_uuid=...` محصولات انتخاب‌شده مزرعه را بگیرید.
5. کاربر محصول و مرحله رشد را انتخاب کند.
6. `POST /api/irrigation/recommend/` را فقط با `farm_uuid` و `plant_name` و `growth_stage` صدا بزنید.
7. برای history از `GET /api/irrigation/recommendations/` و برای جزئیات از `GET /api/irrigation/recommendations/{recommendation_uuid}/` استفاده کنید.

---

# 10) جمع‌بندی سریع endpointها

| Method | Path | کاربرد |
|---|---|---|
| GET | `/api/plants/selected/` | گرفتن محصولات انتخاب‌شده مزرعه |
| GET | `/api/irrigation/` | گرفتن لیست روش‌های آبیاری |
| POST | `/api/irrigation/` | ایجاد روش آبیاری جدید در upstream |
| GET | `/api/irrigation/config/` | گرفتن config اولیه صفحه recommendation |
| POST | `/api/irrigation/recommend/` | تولید recommendation آبیاری |
| GET | `/api/irrigation/recommendations/` | گرفتن history recommendationهای آبیاری |
| GET | `/api/irrigation/recommendations/{recommendation_uuid}/` | گرفتن جزئیات یک recommendation |
| POST | `/api/irrigation/water-stress/` | گرفتن شاخص تنش آبی |
