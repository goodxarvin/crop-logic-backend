# Farmer Todos API

این فایل مستندات کامل APIهای اپ `farmer_todos` را توضیح می‌دهد.

## Base Path

تمام endpointهای این اپ با این prefix در دسترس هستند:

```text
/api/farmer-todos/
```

## Authentication

همه endpointهای این اپ نیاز به احراز هویت دارند.

- Permission: `IsAuthenticated`
- Authentication: بر اساس تنظیمات DRF پروژه، معمولاً JWT

هدر معمول:

```text
Authorization: Bearer <token>
```

## Overview

در ساختار فعلی پروژه، `farmer_todos` و `farmer_calendar` روی یک مدل مشترک سوار هستند، اما این اپ APIهای مخصوص todo را با فرمت مناسب frontend برمی‌گرداند.

موجودیت اصلی:

- `FarmerTodoTask`

فیلدهای مهم response:

- `id`: شناسه عمومی task از نوع UUID
- `title`: عنوان کار
- `zone`: نام ناحیه یا بخش
- `scheduledDate`: تاریخ انجام
- `time`: ساعت انجام
- `priority`: اولویت
- `note`: توضیح task
- `tags`: لیست tagها
- `status`: وضعیت

## Enums

### Priority

اولویت‌ها enum-based هستند و از دیتابیس خوانده نمی‌شوند.

مقادیر نهایی ذخیره‌شده:

- `زیاد`
- `متوسط`
- `کم`

ورودی‌های قابل قبول:

- `high`
- `medium`
- `low`
- `زیاد`
- `متوسط`
- `کم`

### Tags

`tags` هم enum-based هستند و از دیتابیس خوانده نمی‌شوند.

نمونه tagهای مجاز:

- `آبیاری`
- `آفت`
- `فوری`
- `روزانه`
- `ثبت دستی`
- `بازدید`
- `کوددهی`
- `سمپاشی`
- `برداشت`

اگر tag خارج از enum ارسال شود، request با validation error رد می‌شود.

### Status

مقادیر مجاز:

- `open`
- `done`

## Endpoints

### 1) List Tasks

```http
GET /api/farmer-todos/
```

#### Query Params

- `status`: فیلتر بر اساس وضعیت
- `priority`: فیلتر بر اساس اولویت
- `date`: فیلتر دقیق روی تاریخ
- `from`: فیلتر از این تاریخ به بعد
- `to`: فیلتر تا این تاریخ
- `zone`: فیلتر بر اساس zone
- `search`: جستجو در `title` و `note`
- `farm_uuid`: محدود کردن نتایج به یک مزرعه

#### Behavior

- فقط taskهای متعلق به farmهای کاربر login شده را برمی‌گرداند
- `priority` ورودی مثل `high` به مقدار داخلی مثل `زیاد` normalize می‌شود
- `search` در `title` و `description` مدل جستجو می‌کند
- خروجی بر اساس `scheduled_date` و `time` و `created_at` مرتب می‌شود

#### Sample Request

```http
GET /api/farmer-todos/?farm_uuid=<farm_uuid>&priority=high&status=open&search=رطوبت
```

#### Sample Response

```json
{
  "tasks": [
    {
      "id": "11111111-1111-1111-1111-111111111111",
      "title": "بررسی رطوبت ردیف شمالی",
      "zone": "قطعه گندم - شمال مزرعه",
      "scheduledDate": "2025-02-24",
      "time": "06:30",
      "priority": "زیاد",
      "note": "اگر رطوبت کمتر از 28٪ بود، آبیاری دوباره بررسی شود.",
      "tags": ["آبیاری"],
      "status": "open"
    }
  ],
  "meta": {
    "total": 1
  }
}
```

---

### 2) Create Task

```http
POST /api/farmer-todos/
```

#### Request Body

- `title`: اجباری، string
- `zone`: اجباری، string
- `scheduledDate`: اجباری، date با فرمت `YYYY-MM-DD`
- `time`: اجباری، time با فرمت `HH:MM`
- `priority`: اجباری
- `note`: اختیاری، string
- `tags`: اختیاری، array از tagهای enum
- `status`: اختیاری، `open` یا `done`
- `farm_uuid`: اختیاری، اما اگر کاربر چند farm داشته باشد اجباری می‌شود

#### Validation Rules

- `title` نباید خالی باشد
- `zone` نباید خالی باشد
- `priority` باید از enum مجاز باشد
- `tags` باید فقط از enum مجاز باشند
- در create اگر fieldهای اصلی نباشند خطای validation برمی‌گردد

fieldهای اجباری:

- `title`
- `zone`
- `scheduledDate`
- `time`
- `priority`

#### Sample Request

```json
{
  "farm_uuid": "6b7ce8a8-13ec-4a6e-9118-7c298fd2a111",
  "title": "بازدید پمپ جنوب",
  "zone": "انبار مرکزی",
  "scheduledDate": "2025-02-24",
  "time": "07:00",
  "priority": "medium",
  "note": "بعد از ثبت انجام، مورد غیرعادی را یادداشت کن.",
  "tags": ["روزانه", "ثبت دستی"],
  "status": "open"
}
```

#### Sample Success Response

```json
{
  "task": {
    "id": "7aa97f9f-bc4c-49f1-858f-11f3f433a111",
    "title": "بازدید پمپ جنوب",
    "zone": "انبار مرکزی",
    "scheduledDate": "2025-02-24",
    "time": "07:00",
    "priority": "متوسط",
    "note": "بعد از ثبت انجام، مورد غیرعادی را یادداشت کن.",
    "tags": ["روزانه", "ثبت دستی"],
    "status": "open"
  }
}
```

#### Sample Validation Error

```json
{
  "code": "TASK_VALIDATION_ERROR",
  "message": "priority must be one of زیاد, متوسط, کم, high, medium, low",
  "details": {
    "priority": [
      "priority must be one of زیاد, متوسط, کم, high, medium, low"
    ]
  }
}
```

---

### 3) Get Task Detail

```http
GET /api/farmer-todos/<task_uuid>/
```

#### Path Param

- `task_uuid`: شناسه UUID تسک

#### Behavior

- فقط اگر task متعلق به کاربر باشد برگردانده می‌شود
- اگر وجود نداشته باشد یا متعلق به کاربر دیگری باشد، `404` می‌دهد

#### Sample Response

```json
{
  "task": {
    "id": "11111111-1111-1111-1111-111111111111",
    "title": "بررسی رطوبت ردیف شمالی",
    "zone": "قطعه گندم - شمال مزرعه",
    "scheduledDate": "2025-02-24",
    "time": "06:30",
    "priority": "زیاد",
    "note": "اگر رطوبت کمتر از 28٪ بود، آبیاری دوباره بررسی شود.",
    "tags": ["آبیاری"],
    "status": "open"
  }
}
```

#### Sample Not Found Response

```json
{
  "code": "TASK_NOT_FOUND",
  "message": "Task not found."
}
```

---

### 4) Update Task

```http
PUT /api/farmer-todos/<task_uuid>/
```

#### Behavior

- این endpoint از `partial=True` استفاده می‌کند، پس می‌توانی فقط بخشی از فیلدها را بفرستی
- اگر `farm_uuid` ارسال شود، نباید farm فعلی task را تغییر دهد
- اگر `tags` ارسال شوند، لیست tagهای task با لیست جدید جایگزین می‌شود
- اگر `zone` ارسال شود، zone جدید resolve یا ساخته می‌شود

#### Sample Request

```json
{
  "status": "done"
}
```

یا:

```json
{
  "priority": "high",
  "tags": ["فوری", "بازدید"],
  "note": "این کار باید امروز نهایی شود."
}
```

#### Sample Response

```json
{
  "task": {
    "id": "11111111-1111-1111-1111-111111111111",
    "title": "بررسی رطوبت ردیف شمالی",
    "zone": "قطعه گندم - شمال مزرعه",
    "scheduledDate": "2025-02-24",
    "time": "06:30",
    "priority": "زیاد",
    "note": "اگر رطوبت کمتر از 28٪ بود، آبیاری دوباره بررسی شود.",
    "tags": ["آبیاری"],
    "status": "done"
  }
}
```

---

### 5) Delete Task

```http
DELETE /api/farmer-todos/<task_uuid>/
```

#### Sample Response

```json
{
  "success": true
}
```

---

### 6) List Zones

```http
GET /api/farmer-todos/zones/
```

#### Query Params

- `farm_uuid`: اختیاری

#### Behavior

- zoneها از دیتابیس خوانده می‌شوند
- اگر `farm_uuid` ارسال شود، zoneها به همان farm محدود می‌شوند
- اگر `farm_uuid` ارسال نشود، zoneهای تکراری بین farmهای کاربر deduplicate می‌شوند

#### Sample Response

```json
{
  "zones": [
    {
      "id": "zone_gndm-shmal-mzrh",
      "label": "قطعه گندم - شمال مزرعه",
      "value": "قطعه گندم - شمال مزرعه"
    }
  ],
  "meta": {
    "total": 1
  }
}
```

---

### 7) List Tags

```http
GET /api/farmer-todos/tags/
```

#### Query Params

- `farm_uuid`: اختیاری؛ در نسخه فعلی فقط validate می‌شود

#### Behavior

- tagها از enum داخلی کد برمی‌گردند
- این endpoint دیگر از جدول tag چیزی نمی‌خواند

#### Sample Response

```json
{
  "tags": [
    {
      "id": "tag_irrigation",
      "label": "آبیاری",
      "value": "آبیاری"
    },
    {
      "id": "tag_pest",
      "label": "آفت",
      "value": "آفت"
    },
    {
      "id": "tag_urgent",
      "label": "فوری",
      "value": "فوری"
    }
  ],
  "meta": {
    "total": 9
  }
}
```

---

### 8) Summary

```http
GET /api/farmer-todos/summary/
```

#### Query Params

- `farm_uuid`: اختیاری

#### Response Fields

- `todayTasksCount`: تعداد taskهای امروز
- `completedCount`: تعداد taskهای انجام‌شده
- `urgentCount`: تعداد taskهای باز با priority بالا
- `progressValue`: درصد پیشرفت
- `nextTask`: نزدیک‌ترین task باز

#### Behavior

- `progressValue` از نسبت `completedCount / totalCount` محاسبه می‌شود
- `nextTask` اولین task باز از امروز به بعد است

#### Sample Response

```json
{
  "todayTasksCount": 2,
  "completedCount": 1,
  "urgentCount": 2,
  "progressValue": 50,
  "nextTask": {
    "id": "11111111-1111-1111-1111-111111111111",
    "title": "بررسی رطوبت ردیف شمالی",
    "zone": "قطعه گندم - شمال مزرعه",
    "scheduledDate": "2025-02-24",
    "time": "06:30",
    "priority": "زیاد",
    "note": "اگر رطوبت کمتر از 28٪ بود، آبیاری دوباره بررسی شود.",
    "tags": ["آبیاری"],
    "status": "open"
  }
}
```

## Error Format

خطاهای validation:

```json
{
  "code": "TASK_VALIDATION_ERROR",
  "message": "error message",
  "details": {}
}
```

خطای پیدا نشدن:

```json
{
  "code": "TASK_NOT_FOUND",
  "message": "Task not found."
}
```

## Farm Resolution Rules

رفتار `farm_uuid`:

- اگر کاربر فقط یک farm داشته باشد، در create می‌تواند `farm_uuid` نفرستد
- اگر کاربر چند farm داشته باشد، در create باید `farm_uuid` بفرستد
- اگر `farm_uuid` نامعتبر باشد، validation error برمی‌گردد
- در update، `farm_uuid` نباید farm task را تغییر دهد

## Notes

- فایل routeها: `farmer_todos/urls.py`
- فایل viewها: `farmer_todos/views.py`
- فایل serializerها: `farmer_todos/serializers.py`
- enumهای مشترک: `farmer_calendar/enums.py`

## Related Note

در ساختار فعلی پروژه، `farmer_todos` از مدل مشترک با `farmer_calendar` استفاده می‌کند، ولی response و endpointهای این فایل مخصوص todo هستند.
