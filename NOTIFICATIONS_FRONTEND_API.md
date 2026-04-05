# راهنمای استفاده فرانت از APIهای Notifications

این فایل برای تیم فرانت نوشته شده تا بدون بررسی کد بک‌اند، بتواند APIهای ماژول `notifications` را مصرف کند.

---

## خلاصه خیلی کوتاه

- تمام APIهای فعلی نوتیفیکیشن بر اساس `farm_uuid` کار می‌کنند.
- برای گرفتن نوتیفیکیشن‌ها باید `GET /api/notifications/long-poll/` را صدا بزنید.
- در هر آیتم نوتیفیکیشن، فیلد `since_id` برگردانده می‌شود.
- برای علامت‌زدن نوتیفیکیشن‌ها به‌عنوان خوانده‌شده باید `POST /api/notifications/mark-as-read/` را با `farm_uuid` و `slice_id` صدا بزنید.
- هر نوتیفیکیشن دارای وضعیت `is_read` است:
  - `false` یعنی خوانده نشده
  - `true` یعنی خوانده شده

---

## Base Path

```text
/api/notifications/
```

---

## احراز هویت

هر دو API فعلی نیاز به کاربر لاگین‌شده دارند.

یعنی فرانت باید توکن کاربر را مثل بقیه endpointهای protected ارسال کند.

---

## 1) گرفتن نوتیفیکیشن‌ها

### Endpoint

```http
GET /api/notifications/long-poll/?farm_uuid=<farm_uuid>&since_id=<since_id>&timeout=<seconds>
```

### Query Params

| نام | اجباری | توضیح |
|---|---|---|
| `farm_uuid` | بله | شناسه مزرعه انتخاب‌شده |
| `since_id` | خیر | فقط نوتیفیکیشن‌های جدیدتر از این مقدار برگردانده می‌شوند |
| `timeout` | خیر | زمان long-poll بر حسب ثانیه، بین `0` تا `60` |

### رفتار

- اگر `since_id` ارسال نشود، همه نوتیفیکیشن‌های مزرعه برمی‌گردند.
- اگر `since_id` ارسال شود، فقط نوتیفیکیشن‌هایی که `id > since_id` دارند برمی‌گردند.
- اگر نوتیفیکیشن جدیدی وجود نداشته باشد، تا زمان `timeout` منتظر می‌ماند و بعد آرایه خالی برمی‌گرداند.
- این endpoint فقط برای مزرعه‌ای جواب می‌دهد که متعلق به همان کاربر باشد.

### نمونه درخواست

```http
GET /api/notifications/long-poll/?farm_uuid=550e8400-e29b-41d4-a716-446655440000&since_id=12&timeout=15
```

### نمونه response موفق

```json
{
  "code": 200,
  "msg": "success",
  "data": [
    {
      "uuid": "0d4f68d0-8a49-4d5c-9d1c-1d4fd6d5e3a1",
      "farm_uuid": "550e8400-e29b-41d4-a716-446655440000",
      "since_id": 13,
      "title": "هشدار آبیاری",
      "message": "رطوبت خاک پایین است",
      "level": "warning",
      "is_read": false,
      "metadata": {
        "sensor": "soil-1"
      },
      "created_at": "2025-02-20T10:30:00Z"
    }
  ]
}
```

### معنی فیلدهای مهم

| فیلد | توضیح |
|---|---|
| `since_id` | شناسه ترتیبی نوتیفیکیشن برای polling بعدی |
| `is_read` | وضعیت خوانده‌شدن نوتیفیکیشن |
| `level` | سطح نوتیفیکیشن مثل `info`، `warning`، `critical` |
| `metadata` | اطلاعات تکمیلی برای UI یا رفتارهای خاص |

### نکته مهم برای فرانت

بعد از هر بار دریافت response:

1. اگر `data` خالی نبود، `since_id` آخرین آیتم را نگه دارید.
2. در درخواست بعدی، همان مقدار را به‌عنوان `since_id` بفرستید.
3. برای badge یا شمارنده unread، از `is_read` استفاده کنید.

---

## 2) خوانده‌کردن نوتیفیکیشن‌ها

### Endpoint

```http
POST /api/notifications/mark-as-read/
```

### Body

```json
{
  "farm_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "slice_id": 13
}
```

### معنی `slice_id`

`slice_id` یعنی:

- همه نوتیفیکیشن‌های همان مزرعه که `id <= slice_id` دارند
- و هنوز `is_read=false` هستند
- به `is_read=true` تغییر می‌کنند

به بیان ساده، اگر کاربر تا یک نقطه از لیست نوتیفیکیشن‌ها را دیده، فرانت می‌تواند `since_id` آخرین آیتم دیده‌شده را به‌عنوان `slice_id` ارسال کند.

### نمونه response موفق

```json
{
  "code": 200,
  "msg": "success",
  "marked_count": 4
}
```

### معنی `marked_count`

تعداد نوتیفیکیشن‌هایی که واقعا در دیتابیس از unread به read تغییر کرده‌اند.

---

## خطاهای رایج

### مزرعه پیدا نشد

اگر `farm_uuid` متعلق به کاربر نباشد یا وجود نداشته باشد:

```json
{
  "code": 404,
  "msg": "Farm not found."
}
```

### جدول نوتیفیکیشن آماده نیست

اگر migrationهای بک‌اند اجرا نشده باشند:

```json
{
  "code": 503,
  "msg": "Notifications table is not ready. Run migrations."
}
```

---

## پیشنهاد Flow برای فرانت

### سناریوی پیشنهادی

1. کاربر یک مزرعه active انتخاب می‌کند.
2. فرانت `farm_uuid` آن مزرعه را در state نگه می‌دارد.
3. اولین بار:

```http
GET /api/notifications/long-poll/?farm_uuid=<farm_uuid>&timeout=0
```

4. آخرین `since_id` را ذخیره می‌کند.
5. بعد از آن polling را با `since_id` ادامه می‌دهد:

```http
GET /api/notifications/long-poll/?farm_uuid=<farm_uuid>&since_id=<last_since_id>&timeout=15
```

6. وقتی کاربر نوتیفیکیشن‌ها را دید، فرانت آخرین آیتم دیده‌شده را با `slice_id` به endpoint خوانده‌شدن می‌فرستد.

---

## پیشنهاد پیاده‌سازی در فرانت

- برای هر `farm_uuid` یک `last_since_id` جدا نگه دارید.
- لیست نوتیفیکیشن‌ها را per-farm در state نگه دارید.
- unread count را از روی آیتم‌هایی که `is_read=false` دارند محاسبه کنید.
- وقتی کاربر صفحه نوتیفیکیشن را باز کرد یا لیست را تا انتها دید، `slice_id` آخرین آیتم دیده‌شده را ارسال کنید.

---

## routeهای فعال فعلی

| Method | Path | توضیح |
|---|---|---|
| GET | `/api/notifications/long-poll/` | دریافت نوتیفیکیشن‌ها با پشتیبانی از `since_id` |
| POST | `/api/notifications/mark-as-read/` | خوانده‌کردن نوتیفیکیشن‌ها تا `slice_id` |

