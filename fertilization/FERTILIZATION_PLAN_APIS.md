# Fertilization Plan APIs

این فایل APIهای مدیریت برنامه‌های کودی را توضیح می‌دهد.

Base path:

`/api/fertilization/`

این APIها فقط روی برنامه‌های متعلق به کاربر لاگین‌شده عمل می‌کنند.

---

## 1) دریافت لیست برنامه‌های کودی

### Request

- Method: `GET`
- URL: `/api/fertilization/plans/`
- Query params:
  - `farm_uuid` الزامی
  - `page` اختیاری
  - `page_size` اختیاری، حداکثر `100`

### Example

```http
GET /api/fertilization/plans/?farm_uuid=11111111-1111-1111-1111-111111111111&page=1&page_size=10
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
      "title": "برنامه کودی گندم",
      "crop_id": "گندم",
      "plant_name": "گندم",
      "growth_stage": "flowering",
      "is_active": true,
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

---

## 2) دریافت جزئیات یک برنامه کودی

### Request

- Method: `GET`
- URL: `/api/fertilization/plans/{plan_uuid}/`
- Path param:
  - `plan_uuid` الزامی

### Example

```http
GET /api/fertilization/plans/6d6a1f0d-1a9b-4f2f-8fe1-2d73d9d2d9f1/
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
    "title": "برنامه کودی گندم",
    "crop_id": "گندم",
    "plant_name": "گندم",
    "growth_stage": "flowering",
    "is_active": true,
    "created_at": "2025-02-24T10:20:30Z",
    "updated_at": "2025-02-24T10:20:30Z",
    "plan_payload": {
      "title": "برنامه کودی گندم",
      "items": [
        {
          "name": "NPK 20-20-20"
        }
      ]
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

## 3) حذف برنامه کودی

### Request

- Method: `DELETE`
- URL: `/api/fertilization/plans/{plan_uuid}/`

### Example

```http
DELETE /api/fertilization/plans/6d6a1f0d-1a9b-4f2f-8fe1-2d73d9d2d9f1/
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

## 4) تغییر وضعیت فعال بودن برنامه کودی

### Request

- Method: `PATCH`
- URL: `/api/fertilization/plans/{plan_uuid}/status/`
- Body:
  - `is_active` الزامی، `boolean`

### Example

```http
PATCH /api/fertilization/plans/6d6a1f0d-1a9b-4f2f-8fe1-2d73d9d2d9f1/status/
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
    "is_active": false
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

- `GET /api/fertilization/plans/` لیست برنامه‌ها
- `GET /api/fertilization/plans/{plan_uuid}/` جزئیات برنامه
- `DELETE /api/fertilization/plans/{plan_uuid}/` حذف نرم برنامه
- `PATCH /api/fertilization/plans/{plan_uuid}/status/` فعال/غیرفعال کردن برنامه
