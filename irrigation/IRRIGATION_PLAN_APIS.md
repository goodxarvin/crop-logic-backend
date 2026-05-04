# Irrigation Plan APIs

این فایل APIهای مدیریت برنامه‌های آبیاری را توضیح می‌دهد.

Base path:

`/api/irrigation/`

این APIها فقط روی برنامه‌های متعلق به کاربر لاگین‌شده عمل می‌کنند.

---

## 1) دریافت لیست برنامه‌های آبیاری

### Request

- Method: `GET`
- URL: `/api/irrigation/plans/`
- Query params:
  - `farm_uuid` الزامی
  - `page` اختیاری
  - `page_size` اختیاری، حداکثر `100`

### Example

```http
GET /api/irrigation/plans/?farm_uuid=11111111-1111-1111-1111-111111111111&page=1&page_size=10
```

### Success Response

```json
{
  "code": 200,
  "msg": "success",
  "data": [
    {
      "plan_uuid": "6d6a1f0d-1a9b-4f2f-8fe1-2d73d9d2d9f1",
      "source": "free_text",
      "source_label": "متن آزاد کاربر",
      "title": "برنامه آبیاری گندم",
      "crop_id": "گندم",
      "plant_name": "گندم",
      "growth_stage": "flowering",
      "is_active": false,
      "created_at": "2025-02-24T10:20:30Z"
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

### Notes

- فقط planهایی برگردانده می‌شوند که `is_deleted=False` باشند.
- ترتیب لیست از جدید به قدیم است.
- در هر مزرعه، در هر نوع plan فقط یک plan می‌تواند `is_active=true` باشد.

---

## 2) دریافت جزئیات یک برنامه آبیاری

### Request

- Method: `GET`
- URL: `/api/irrigation/plans/{plan_uuid}/`
- Path param:
  - `plan_uuid` الزامی

### Example

```http
GET /api/irrigation/plans/6d6a1f0d-1a9b-4f2f-8fe1-2d73d9d2d9f1/
```

### Success Response

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "plan_uuid": "6d6a1f0d-1a9b-4f2f-8fe1-2d73d9d2d9f1",
    "source": "free_text",
    "source_label": "متن آزاد کاربر",
    "title": "برنامه آبیاری گندم",
    "crop_id": "گندم",
    "plant_name": "گندم",
    "growth_stage": "flowering",
    "is_active": false,
    "created_at": "2025-02-24T10:20:30Z",
    "updated_at": "2025-02-24T10:20:30Z",
    "plan_payload": {
      "plan": {
        "durationMinutes": 25
      }
    }
  }
}
```

### Not Found

```json
{
  "code": 404,
  "msg": "Plan not found."
}
```

### Notes

- فقط اگر plan متعلق به کاربر باشد و حذف نشده باشد برگردانده می‌شود.

---

## 3) حذف برنامه آبیاری

### Request

- Method: `DELETE`
- URL: `/api/irrigation/plans/{plan_uuid}/`

### Example

```http
DELETE /api/irrigation/plans/6d6a1f0d-1a9b-4f2f-8fe1-2d73d9d2d9f1/
```

### Success Response

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "plan_uuid": "6d6a1f0d-1a9b-4f2f-8fe1-2d73d9d2d9f1",
    "is_deleted": true
  }
}
```

### Behavior

- حذف به‌صورت `soft delete` انجام می‌شود.
- در عمل:
  - `is_deleted = true`
  - `is_active = false`
  - `deleted_at` مقداردهی می‌شود

### Not Found

```json
{
  "code": 404,
  "msg": "Plan not found."
}
```

---

## 4) تغییر وضعیت فعال بودن برنامه آبیاری

### Request

- Method: `PATCH`
- URL: `/api/irrigation/plans/{plan_uuid}/status/`
- Body:
  - `is_active` الزامی، `boolean`

### Example

```http
PATCH /api/irrigation/plans/6d6a1f0d-1a9b-4f2f-8fe1-2d73d9d2d9f1/status/
Content-Type: application/json

{
  "is_active": false
}
```

### Success Response

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "plan_uuid": "6d6a1f0d-1a9b-4f2f-8fe1-2d73d9d2d9f1",
    "is_active": true
  }
}
```

### Validation Error

```json
{
  "is_active": [
    "This field is required."
  ]
}
```

### Not Found

```json
{
  "code": 404,
  "msg": "Plan not found."
}
```

---

## Summary

- planهای جدید به‌صورت پیش‌فرض `inactive` ساخته می‌شوند.
- در هر مزرعه فقط یک plan از این نوع می‌تواند `active` باشد.
- `GET /api/irrigation/plans/` لیست برنامه‌ها
- `GET /api/irrigation/plans/{plan_uuid}/` جزئیات برنامه
- `DELETE /api/irrigation/plans/{plan_uuid}/` حذف نرم برنامه
- `PATCH /api/irrigation/plans/{plan_uuid}/status/` فعال/غیرفعال کردن برنامه
