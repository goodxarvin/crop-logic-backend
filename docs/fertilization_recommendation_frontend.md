# Fertilization Recommendation History APIs

این فایل برای تیم فرانت نوشته شده تا بتواند از APIهای history توصیه های کودهی استفاده کند.

## وضعیت recommendation

هر recommendation یک status دارد.

### statusهای ممکن

- `pending_confirmation` → `منتظر تایید`
- `in_progress` → `در حال مصرف`
- `completed` → `پایان یافته`

### وضعیت فعلی سیستم

فعلاً همه recommendationهای جدید و recommendationهای قبلی که migrate شده اند با وضعیت زیر ذخیره می شوند:

- `pending_confirmation`
- برچسب نمایشی: `منتظر تایید`

فرانت باید `status` را برای منطق برنامه و `status_label` را برای نمایش مستقیم استفاده کند.

---

## 1) لیست توصیه های کودهی یک مزرعه

### Endpoint

`GET /api/fertilization/recommendations/?farm_uuid=<farm_uuid>`

### کاربرد

- نمایش history توصیه های کودهی یک مزرعه
- ساخت جدول یا لیست برای مشاهده توصیه های قبلی
- نمایش badge وضعیت recommendation
- ورود به صفحه جزئیات هر recommendation

### Query Params

- `farm_uuid`: شناسه مزرعه
- `crop_id`: شناسه یا نام محصول. این فیلد همان plant name است و مستقیم برای AI هم ارسال می شود
- `page`: شماره صفحه، شروع از `1`
- `page_size`: تعداد آیتم در هر صفحه، بین `1` تا `100`

### هدرها

- `Authorization: Bearer <token>`
- `Accept: application/json`

### نمونه درخواست

```bash
curl -X GET \
  'http://localhost:8000/api/fertilization/recommendations/?farm_uuid=11111111-1111-1111-1111-111111111111&page=1&page_size=10' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <token>'
```

### نمونه پاسخ موفق

```json
{
  "code": 200,
  "msg": "success",
  "data": [
    {
      "recommendation_uuid": "4d595ee0-9dbb-4c50-a871-2b4359d0d748",
      "crop_id": "گندم",
      "plant_name": "گندم",
      "growth_stage": "vegetative",
      "fertilizer_type": "NPK",
      "status": "pending_confirmation",
      "status_label": "منتظر تایید",
      "requested_at": "2025-01-10T08:30:00Z"
    },
    {
      "recommendation_uuid": "bbdf0d50-0f78-4099-a4d3-b1c4aa54eeb9",
      "crop_id": "ذرت",
      "plant_name": "ذرت",
      "growth_stage": "flowering",
      "fertilizer_type": "Micronutrient",
      "status": "pending_confirmation",
      "status_label": "منتظر تایید",
      "requested_at": "2025-01-08T09:10:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_pages": 3,
    "total_items": 25,
    "has_next": true,
    "has_previous": false,
    "next": "http://localhost:8000/api/fertilization/recommendations/?farm_uuid=11111111-1111-1111-1111-111111111111&page=2&page_size=10",
    "previous": null
  }
}
```

### فیلدهای `data[]`

- `recommendation_uuid`: شناسه یکتای recommendation برای گرفتن جزئیات
- `crop_id`: شناسه یا نام محصول ثبت شده در recommendation
- `plant_name`: معادل نمایشی `crop_id` برای سازگاری با فرانت
- `growth_stage`: مرحله رشد در زمان ثبت recommendation
- `fertilizer_type`: نوع کود پیشنهادی مثل `NPK`
- `status`: کد وضعیت recommendation
- `status_label`: متن نمایشی وضعیت recommendation
- `requested_at`: زمان ثبت recommendation

### فیلدهای `pagination`

- `page`: صفحه فعلی
- `page_size`: تعداد آیتم در هر صفحه
- `total_pages`: تعداد کل صفحات
- `total_items`: تعداد کل recommendationها
- `has_next`: آیا صفحه بعدی وجود دارد یا نه
- `has_previous`: آیا صفحه قبلی وجود دارد یا نه
- `next`: لینک صفحه بعدی
- `previous`: لینک صفحه قبلی

### پیشنهاد نمایش status در UI

- `pending_confirmation` → badge زرد یا خاکستری روشن
- `in_progress` → badge آبی یا سبز
- `completed` → badge خاکستری یا سفید

### خطاهای رایج

#### مزرعه پیدا نشد

```json
{
  "farm_uuid": [
    "Farm not found."
  ]
}
```

#### پارامترهای pagination نامعتبر

```json
{
  "page": [
    "Ensure this value is greater than or equal to 1."
  ]
}
```

---

## 2) جزئیات یک recommendation

### Endpoint

`GET /api/fertilization/recommendations/<recommendation_uuid>/`

### کاربرد

- نمایش کامل جزئیات recommendation
- باز کردن صفحه detail یا modal recommendation
- replay کردن خروجی recommendation بدون نیاز به درخواست مجدد از AI

### Path Param

- `recommendation_uuid`: شناسه recommendation از API لیست

### نکته مهم برای محصول

- فیلد اصلی محصول در این ماژول `crop_id` است
- `crop_id` همان plant name است
- بک اند همان `crop_id` را مستقیم برای AI ارسال می کند
- `plant_name` در response فقط برای سازگاری فرانت نگه داشته شده و مقدارش برابر `crop_id` است

### هدرها

- `Authorization: Bearer <token>`
- `Accept: application/json`

### نمونه درخواست

```bash
curl -X GET \
  'http://localhost:8000/api/fertilization/recommendations/4d595ee0-9dbb-4c50-a871-2b4359d0d748/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <token>'
```

### نمونه پاسخ موفق

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "crop_id": "گندم",
    "plant_name": "گندم",
    "growth_stage": "vegetative",
    "status": "pending_confirmation",
    "status_label": "منتظر تایید",
    "primary_recommendation": {
      "fertilizer_code": "npk-202020",
      "fertilizer_name": "NPK 20-20-20",
      "display_title": "کود کامل متعادل",
      "fertilizer_type": "NPK",
      "npk_ratio": {
        "n": 20,
        "p": 20,
        "k": 20,
        "label": "20-20-20"
      },
      "application_method": {
        "id": "fertigation",
        "label": "کودآبیاری"
      },
      "application_interval": {
        "value": 14,
        "unit": "day",
        "label": "هر 14 روز"
      },
      "dosage": {
        "base_amount_per_hectare": 65,
        "base_amount_per_square_meter": 0.0065,
        "unit": "kg",
        "label": "65 کیلوگرم در هکتار",
        "calculation_basis": "engine-v2"
      },
      "reasoning": "متعادل برای فاز رشد",
      "summary": "مصرف منظم در این مرحله توصیه می شود"
    },
    "nutrient_analysis": {
      "macro": [
        {
          "key": "n",
          "name": "Nitrogen",
          "value": 20,
          "unit": "percent",
          "description": "تقویت رشد رویشی"
        }
      ],
      "micro": []
    },
    "application_guide": {
      "safety_warning": "در ساعات خنک مصرف شود",
      "steps": [
        {
          "step_number": 1,
          "title": "حل کردن",
          "description": "کود را در آب حل کنید"
        }
      ]
    },
    "alternative_recommendations": [
      {
        "fertilizer_code": "npk-121236",
        "fertilizer_name": "NPK 12-12-36",
        "fertilizer_type": "NPK",
        "usage_method": "fertigation",
        "description": "برای نیاز پتاس بالا"
      }
    ],
    "sections": [
      {
        "type": "recommendation",
        "title": "پیشنهاد اصلی",
        "icon": "leaf",
        "content": "NPK 20-20-20"
      }
    ]
  }
}
```

### نکته مهم

این response دقیقا همان ساختار endpoint زیر را برمی گرداند:

`POST /api/fertilization/recommend/`

یعنی فرانت می تواند برای صفحه detail همان componentهایی را استفاده کند که برای recommendation اصلی استفاده می کند.

### خطای رایج

#### recommendation پیدا نشد

```json
{
  "code": 404,
  "msg": "Recommendation not found."
}
```

---

## پیشنهاد پیاده سازی در فرانت

### برای صفحه history

- ابتدا API لیست را با `farm_uuid` صدا بزنید
- `data` را در جدول یا کارت لیست نمایش دهید
- `status_label` را مستقیم در badge یا chip نشان دهید
- اگر لازم بود رفتار UI بر اساس وضعیت تغییر کند، از `status` استفاده کنید
- با `pagination.page` و `pagination.total_pages` صفحه بندی را بسازید
- روی هر آیتم با `recommendation_uuid` به صفحه detail بروید

### برای صفحه detail

- `recommendation_uuid` را از route بگیرید
- API جزئیات را صدا بزنید
- `data.primary_recommendation` را در Hero/Card اصلی نمایش دهید
- `data.nutrient_analysis` را در بخش تحلیل عناصر نمایش دهید
- `data.application_guide` را در بخش راهنمای مصرف نمایش دهید
- `data.alternative_recommendations` را برای جایگزین ها نمایش دهید
- در صورت نیاز برای سازگاری، از `data.sections` هم استفاده کنید

### فرمول محاسبه مقدار مصرف

```text
مقدار کل = base_amount_per_square_meter × مساحت مزرعه
```

---

## خلاصه مسیرها

- لیست recommendationها:
  - `GET /api/fertilization/recommendations/?farm_uuid=<farm_uuid>&page=1&page_size=10`
- جزئیات recommendation:
  - `GET /api/fertilization/recommendations/<recommendation_uuid>/`
