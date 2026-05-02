# Farmer Calendar API

این فایل مستندات کامل APIهای اپ `farmer_calendar` را توضیح می‌دهد.

## Base Path

تمام endpointهای این اپ با این prefix در دسترس هستند:

```text
/api/events/
```

## Authentication

همه endpointهای این اپ نیاز به احراز هویت دارند.

- Permission: `IsAuthenticated`
- Authentication: بر اساس تنظیمات DRF پروژه، معمولاً JWT

هدر معمول:

```text
Authorization: Bearer <token>
```

## Data Model

موجودیت اصلی در این اپ `FarmerCalendarEvent` است.

فیلدهای مهم:

- `id`: شناسه عمومی event از نوع UUID
- `title`: عنوان event
- `description`: توضیحات
- `deadline`: مهلت به صورت timestamp عددی
- `start`: زمان شروع event
- `end`: زمان پایان event
- `extendedProps`: داده‌های اضافه به صورت object
- `tags`: لیست tagها

## Tag Rules

در نسخه فعلی، `tags` از دیتابیس خوانده نمی‌شوند و فقط از enum داخلی پروژه مجاز هستند.

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

اگر tag خارج از enum ارسال شود، request با خطای validation رد می‌شود.

## Priority

در مدل مشترک event/todo، اولویت به صورت enum تعریف شده است.

مقادیر مجاز:

- `زیاد`
- `متوسط`
- `کم`

یا در بعضی serializerهای مرتبط، ورودی انگلیسی:

- `high`
- `medium`
- `low`

## Endpoints

### 1) List Events

```http
GET /api/events/
```

#### Query Params

- `start`: فیلتر از این datetime به بعد
- `end`: فیلتر تا این datetime
- `farm_uuid`: اگر کاربر چند مزرعه داشته باشد، برای محدود کردن نتایج به یک مزرعه

#### Behavior

- فقط eventهای متعلق به farmهای کاربر login شده را برمی‌گرداند
- اگر `start` ارسال شود، eventهایی برمی‌گردند که `end >= start`
- اگر `end` ارسال شود، eventهایی برمی‌گردند که `start <= end`
- خروجی بر اساس `start` و بعد `created_at` مرتب می‌شود

#### Sample Request

```http
GET /api/events/?farm_uuid=<farm_uuid>&start=2025-02-24T00:00:00Z&end=2025-02-25T00:00:00Z
```

#### Sample Response

```json
{
  "events": [
    {
      "id": "4be7c204-6fd8-4aa4-a5f4-7f0e9ceaa111",
      "title": "آبیاری بلوک شمالی",
      "description": "کنترل فشار و مدت زمان آبیاری",
      "deadline": 1734942600,
      "tags": ["آبیاری", "فوری"],
      "start": "2025-02-24T06:30:00Z",
      "end": "2025-02-24T08:00:00Z",
      "extendedProps": {
        "source": "manual"
      }
    }
  ],
  "meta": {
    "total": 1
  }
}
```

---

### 2) Create Event

```http
POST /api/events/
```

#### Request Body

- `title`: اجباری، string
- `description`: اختیاری، string
- `deadline`: اختیاری، integer
- `tags`: اختیاری، array از tagهای enum
- `start`: اجباری، datetime
- `end`: اجباری، datetime
- `extendedProps`: اختیاری، object
- `farm_uuid`: اختیاری، اما اگر کاربر چند farm داشته باشد اجباری می‌شود

#### Validation Rules

- `title` نباید خالی باشد
- `extendedProps` باید object باشد
- `end` نباید از `start` کوچک‌تر باشد
- `tags` فقط باید از enum مجاز باشند
- اگر کاربر چند farm داشته باشد و `farm_uuid` نفرستد، خطا برمی‌گردد

#### Sample Request

```json
{
  "farm_uuid": "6b7ce8a8-13ec-4a6e-9118-7c298fd2a111",
  "title": "بازدید آفت در گلخانه",
  "description": "بررسی وضعیت برگ ها و ثبت گزارش",
  "deadline": 1734971400,
  "tags": ["آفت", "فوری"],
  "start": "2025-02-24T14:00:00Z",
  "end": "2025-02-24T15:00:00Z",
  "extendedProps": {
    "source": "manual"
  }
}
```

#### Sample Success Response

```json
{
  "event": {
    "id": "7aa97f9f-bc4c-49f1-858f-11f3f433a111",
    "title": "بازدید آفت در گلخانه",
    "description": "بررسی وضعیت برگ ها و ثبت گزارش",
    "deadline": 1734971400,
    "tags": ["آفت", "فوری"],
    "start": "2025-02-24T14:00:00Z",
    "end": "2025-02-24T15:00:00Z",
    "extendedProps": {
      "source": "manual"
    }
  }
}
```

#### Sample Validation Error

```json
{
  "code": "EVENT_VALIDATION_ERROR",
  "message": "title cannot be empty",
  "details": {
    "title": ["title cannot be empty"]
  }
}
```

---

### 3) Get Event Detail

```http
GET /api/events/<event_uuid>/
```

#### Path Param

- `event_uuid`: شناسه UUID رویداد

#### Behavior

- فقط اگر event متعلق به کاربر باشد برگردانده می‌شود
- اگر وجود نداشته باشد یا متعلق به کاربر دیگری باشد، `404` می‌دهد

#### Sample Response

```json
{
  "event": {
    "id": "4be7c204-6fd8-4aa4-a5f4-7f0e9ceaa111",
    "title": "آبیاری بلوک شمالی",
    "description": "کنترل فشار و مدت زمان آبیاری",
    "deadline": 1734942600,
    "tags": ["آبیاری"],
    "start": "2025-02-24T06:30:00Z",
    "end": "2025-02-24T08:00:00Z",
    "extendedProps": {}
  }
}
```

#### Sample Not Found Response

```json
{
  "code": "EVENT_NOT_FOUND",
  "message": "Event not found."
}
```

---

### 4) Update Event

```http
PUT /api/events/<event_uuid>/
```

#### Request Body

ساختار body مثل create است.

#### Important Notes

- این endpoint در حال حاضر update کامل انجام می‌دهد، نه partial
- اگر `farm_uuid` ارسال شود، نباید با farm فعلی event فرق داشته باشد
- اگر `tags` ارسال شوند، tagهای قبلی با همان لیست جدید جایگزین می‌شوند

#### Sample Request

```json
{
  "title": "آبیاری بلوک شمالی",
  "description": "اولویت بالا",
  "deadline": 1734942600,
  "tags": ["آبیاری", "فوری"],
  "start": "2025-02-24T15:00:00Z",
  "end": "2025-02-24T16:00:00Z",
  "extendedProps": {}
}
```

#### Sample Response

```json
{
  "event": {
    "id": "4be7c204-6fd8-4aa4-a5f4-7f0e9ceaa111",
    "title": "آبیاری بلوک شمالی",
    "description": "اولویت بالا",
    "deadline": 1734942600,
    "tags": ["آبیاری", "فوری"],
    "start": "2025-02-24T15:00:00Z",
    "end": "2025-02-24T16:00:00Z",
    "extendedProps": {}
  }
}
```

---

### 5) Delete Event

```http
DELETE /api/events/<event_uuid>/
```

#### Sample Response

```json
{
  "success": true
}
```

---

### 6) List Available Tags

```http
GET /api/events/tags/
```

#### Query Params

- `farm_uuid`: اختیاری؛ در نسخه فعلی فقط validate می‌شود ولی لیست tagها از enum داخلی برمی‌گردد

#### Behavior

- tagها از enum کد برمی‌گردند
- این endpoint دیگر به داده‌های tag در دیتابیس وابسته نیست

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

## Error Format

فرمت خطاهای validation به این شکل است:

```json
{
  "code": "EVENT_VALIDATION_ERROR",
  "message": "error message",
  "details": {}
}
```

و خطای پیدا نشدن:

```json
{
  "code": "EVENT_NOT_FOUND",
  "message": "Event not found."
}
```

## Farm Resolution Rules

رفتار `farm_uuid` در این اپ:

- اگر کاربر فقط یک farm داشته باشد، در create می‌تواند `farm_uuid` نفرستد
- اگر کاربر چند farm داشته باشد، در create باید `farm_uuid` بفرستد
- اگر `farm_uuid` نامعتبر باشد، validation error برمی‌گردد
- در update، `farm_uuid` نباید farm event را تغییر دهد

## Implementation Notes

- فایل routeها: `farmer_calendar/urls.py`
- فایل viewها: `farmer_calendar/views.py`
- فایل serializerها: `farmer_calendar/serializers.py`
- enumهای tag و priority: `farmer_calendar/enums.py`

## Related Note

در ساختار فعلی پروژه، `farmer_calendar` و `farmer_todos` روی یک مدل مشترک سوار شده‌اند، ولی endpointهای این فایل فقط مربوط به مسیرهای `farmer_calendar` هستند.
