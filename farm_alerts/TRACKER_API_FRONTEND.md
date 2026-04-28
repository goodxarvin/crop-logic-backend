# راهنمای فرانت برای API هشدارهای مزرعه

این سند برای تیم فرانت نوشته شده تا بداند endpoint `tracker` چه ورودی‌ای می‌گیرد، چه کاری انجام می‌دهد، و response آن را چطور باید در UI مصرف کند.

## Endpoint

- `POST /api/farm-alerts/tracker/`

## احراز هویت

- این API نیاز به `Bearer Token` دارد.
- کاربر فقط به مزرعه‌های متعلق به خودش دسترسی دارد.

## کاربرد API

فرانت با ارسال alertهای جدید مربوط به یک مزرعه:

- alertها را در بک‌اند ذخیره می‌کند
- notificationهای 3 روز اخیر همان مزرعه را هم به context اضافه می‌کند
- همه داده‌ها را برای AI می‌فرستد
- AI یک جمع‌بندی کوتاه، وضعیت کلی، و notificationهای مهم برمی‌گرداند
- notificationهای خروجی AI هم در دیتابیس ذخیره می‌شوند

این endpoint هم برای تحلیل وضعیت هشدارها مناسب است، هم برای ساخت کارت summary، هم برای notification center.

## Request Body

فیلدهای ورودی:

- `farm_uuid`: شناسه مزرعه - اجباری
- `alerts`: لیست هشدارهای جدید - اختیاری

### ساختار هر alert

هر آیتم داخل `alerts` می‌تواند این فیلدها را داشته باشد:

- `alert_id`: شناسه یکتای هشدار در سمت منبع یا فرانت
- `level`: شدت هشدار مثل `info`، `warning`، `danger`
- `title`: عنوان هشدار
- `message`: متن هشدار
- `suggested_action`: اقدام پیشنهادی
- `source_metric_type`: نوع شاخص مثل `moisture`
- `timestamp`: زمان هشدار با فرمت datetime - اختیاری
- `payload`: داده تکمیلی JSON - اختیاری

## نمونه request

```json
{
  "farm_uuid": "11111111-1111-1111-1111-111111111111",
  "alerts": [
    {
      "alert_id": "soil-moisture-001",
      "level": "warning",
      "title": "افت رطوبت خاک",
      "message": "رطوبت خاک کمتر از حد مطلوب گزارش شده است.",
      "suggested_action": "آبیاری اصلاحی بررسی شود.",
      "source_metric_type": "moisture"
    }
  ]
}
```

## نمونه curl

```bash
curl -X POST \
  'http://localhost:8000/api/farm-alerts/tracker/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <access_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "farm_uuid": "11111111-1111-1111-1111-111111111111",
    "alerts": [
      {
        "alert_id": "soil-moisture-001",
        "level": "warning",
        "title": "افت رطوبت خاک",
        "message": "رطوبت خاک کمتر از حد مطلوب گزارش شده است.",
        "suggested_action": "آبیاری اصلاحی بررسی شود.",
        "source_metric_type": "moisture"
      }
    ]
  }'
```

## رفتار بک‌اند

بعد از دریافت request:

1. مزرعه را با `farm_uuid` پیدا می‌کند و ownership را چک می‌کند.
2. alertهای ارسالی را در جدول `farm_alerts` ذخیره می‌کند.
3. حداکثر 10 notification ثبت‌شده در 3 روز اخیر همان مزرعه را برمی‌دارد.
4. `alerts` جدید + `recent_notifications` را برای AI می‌فرستد.
5. notificationهای مهم تولیدشده توسط AI را در جدول `farm_notifications` ذخیره می‌کند.
6. response نهایی را به فرانت برمی‌گرداند.

## ساختار response موفق

response داخل envelope استاندارد برمی‌گردد:

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "farm_uuid": "11111111-1111-1111-1111-111111111111",
    "service_id": "farm_alerts",
    "tracker": {},
    "headline": "بررسی رطوبت خاک در مزرعه",
    "overview": "افت خفیف رطوبت خاک گزارش شده است که نیاز به پایش دارد.",
    "status_level": "warning",
    "notifications": [],
    "raw_llm_response": "...",
    "structured_context": {}
  }
}
```

## توضیح فیلدهای اصلی response

### `farm_uuid`

شناسه مزرعه‌ای که تحلیل برای آن انجام شده است.

### `service_id`

شناسه سرویس. فعلا مقدار آن `farm_alerts` است.

### `tracker`

بخش اصلی داده برای ساخت UI هشدارها.

این بخش ممکن است شامل این فیلدها باشد:

- `totalAlerts`: تعداد کل alertهای فعلی
- `alerts`: لیست alertهای تحلیل‌شده
- `alertStats`: آمار خلاصه برای کارت‌ها
- `alertClusters`: گروه‌بندی alertها
- `mostCriticalIssue`: مهم‌ترین هشدار فعلی
- `prioritizedAlertSummaries`: خلاصه‌های اولویت‌دار
- `recommendedOperationalActions`: اقدام‌های عملیاتی پیشنهادی
- `humanReadableExplanations`: توضیح‌های متنی ساده برای کاربر

### `headline`

تیتر کوتاه برای بالای کارت یا صفحه.

### `overview`

جمع‌بندی کوتاه و اجرایی برای کاربر.

### `status_level`

وضعیت کلی تحلیل برای رنگ‌بندی UI.

مقادیر معمول:

- `info`
- `warning`
- `error`
- `success`

### `notifications`

لیست notificationهای مهمی که AI تولید کرده و در دیتابیس ذخیره شده‌اند.

هر notification ممکن است این فیلدها را داشته باشد:

- `id`: شناسه دیتابیسی
- `uuid`: شناسه یکتا
- `farm_uuid`: شناسه مزرعه
- `since_id`: همان `id` برای برخی flowهای polling
- `endpoint`: منبع notification، اینجا معمولا `tracker`
- `title`: عنوان
- `message`: متن
- `level`: شدت
- `suggested_action`: اقدام پیشنهادی
- `source_alert_id`: شناسه alert اصلی
- `source_metric_type`: نوع شاخص
- `payload`: داده تکمیلی
- `is_read`: خوانده شده یا نه
- `metadata`: اطلاعات داخلی
- `created_at`: زمان ایجاد
- `updated_at`: زمان آخرین به‌روزرسانی

### `raw_llm_response`

پاسخ خام AI برای debug یا audit.

برای UI اصلی معمولا لازم نیست مستقیم نمایش داده شود.

### `structured_context`

context تکمیلی که برای AI ساخته شده.

ممکن است شامل این بخش‌ها باشد:

- `farm_profile`
- `tracker`
- `forecasts`
- `incoming_alerts`

این فیلد بیشتر برای debug، مانیتورینگ، یا صفحه‌های تخصصی مفید است.

## استفاده پیشنهادی در فرانت

### هدر صفحه یا کارت summary

از این فیلدها استفاده کنید:

- `headline`
- `overview`
- `status_level`

### لیست هشدارهای فعلی

از:

- `tracker.alerts`

### مهم‌ترین هشدار

از:

- `tracker.mostCriticalIssue`

### کارت آمار هشدار

از:

- `tracker.totalAlerts`
- `tracker.alertStats`

### اقدام‌های پیشنهادی

از:

- `tracker.recommendedOperationalActions`

### توضیح ساده برای کاربر

از:

- `tracker.humanReadableExplanations`

### notification center یا drawer

از:

- `notifications`

## نمونه mapping برای فرانت

```ts
const result = response.data.data;

const headerTitle = result.headline;
const headerText = result.overview;
const severity = result.status_level;

const totalAlerts = result.tracker.totalAlerts;
const alerts = result.tracker.alerts;
const stats = result.tracker.alertStats;
const criticalIssue = result.tracker.mostCriticalIssue;
const suggestedActions = result.tracker.recommendedOperationalActions;
const notifications = result.notifications;
```

## نمونه response واقعی

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "farm_uuid": "11111111-1111-1111-1111-111111111111",
    "service_id": "farm_alerts",
    "tracker": {
      "totalAlerts": 1,
      "alerts": [
        {
          "metric_type": "moisture",
          "title": "تنش رطوبتی",
          "current_value": 42.3,
          "threshold_value": 45,
          "severity": "low",
          "duration_hours": 2.8,
          "duration": "3 ساعت",
          "timestamp": "2026-04-28T20:31:39.594431+00:00",
          "sensor_id": "11111111-1111-1111-1111-111111111111",
          "zone_id": null,
          "domain": "water_balance",
          "direction": "below",
          "unit": "%",
          "icon": "tabler-droplet-half-2",
          "summary": "افت رطوبت خاک ثبت شده و نیاز به پایش نزدیک‌تر دارد.",
          "recommended_action": "روند رطوبت را در نوبت بعدی کنترل و یکنواختی آبیاری را بررسی کنید.",
          "explanation": "رطوبت فعلی 42.3% به زیر آستانه 45.0% رسیده است و این وضعیت 3 ساعت ادامه داشته است.",
          "metadata": {}
        }
      ],
      "alertStats": [
        {
          "title": "تنش رطوبتی",
          "count": "1",
          "avatarColor": "info",
          "avatarIcon": "tabler-droplet-half-2",
          "severity": "low",
          "topSummary": "افت رطوبت خاک ثبت شده و نیاز به پایش نزدیک‌تر دارد."
        }
      ],
      "alertClusters": [
        {
          "domain": "water_balance",
          "title": "تعادل آب",
          "alert_count": 1,
          "highest_severity": "low",
          "primary_metric": "moisture",
          "summary": "افت رطوبت خاک ثبت شده و نیاز به پایش نزدیک‌تر دارد.",
          "alert_ids": [
            "moisture:2026-04-28T20:31:39.594431+00:00"
          ]
        }
      ],
      "mostCriticalIssue": {
        "metric_type": "moisture",
        "title": "تنش رطوبتی",
        "current_value": 42.3,
        "threshold_value": 45,
        "severity": "low",
        "duration_hours": 2.8,
        "duration": "3 ساعت",
        "timestamp": "2026-04-28T20:31:39.594431+00:00",
        "sensor_id": "11111111-1111-1111-1111-111111111111",
        "zone_id": null,
        "domain": "water_balance",
        "direction": "below",
        "unit": "%",
        "icon": "tabler-droplet-half-2",
        "summary": "افت رطوبت خاک ثبت شده و نیاز به پایش نزدیک‌تر دارد.",
        "recommended_action": "روند رطوبت را در نوبت بعدی کنترل و یکنواختی آبیاری را بررسی کنید.",
        "explanation": "رطوبت فعلی 42.3% به زیر آستانه 45.0% رسیده است و این وضعیت 3 ساعت ادامه داشته است.",
        "metadata": {}
      },
      "prioritizedAlertSummaries": [
        "افت رطوبت خاک ثبت شده و نیاز به پایش نزدیک‌تر دارد."
      ],
      "recommendedOperationalActions": [
        "روند رطوبت را در نوبت بعدی کنترل و یکنواختی آبیاری را بررسی کنید."
      ],
      "humanReadableExplanations": [
        "رطوبت فعلی 42.3% به زیر آستانه 45.0% رسیده است و این وضعیت 3 ساعت ادامه داشته است."
      ]
    },
    "headline": "بررسی رطوبت خاک در مزرعه",
    "overview": "افت خفیف رطوبت خاک گزارش شده است که نیاز به پایش دارد.",
    "status_level": "warning",
    "notifications": [
      {
        "id": 1,
        "uuid": "640e6187-49d9-4256-ad0d-18927712d496",
        "farm_uuid": "11111111-1111-1111-1111-111111111111",
        "since_id": 1,
        "endpoint": "tracker",
        "title": "افت رطوبت خاک",
        "message": "رطوبت خاک کمتر از حد مطلوب گزارش شده است.",
        "level": "warning",
        "suggested_action": "روند رطوبت را در نوبت بعدی کنترل و یکنواختی آبیاری را بررسی کنید.",
        "source_alert_id": "soil-moisture-001",
        "source_metric_type": "moisture",
        "payload": {},
        "is_read": false,
        "metadata": {
          "source": "farm_alerts_tracker_ai"
        },
        "created_at": "2026-04-28T23:20:19.750658Z",
        "updated_at": "2026-04-28T23:20:19.750719Z"
      }
    ],
    "raw_llm_response": "{...}",
    "structured_context": {
      "incoming_alerts": [
        {
          "alert_id": "soil-moisture-001",
          "level": "warning",
          "title": "افت رطوبت خاک",
          "message": "رطوبت خاک کمتر از حد مطلوب گزارش شده است.",
          "suggested_action": "آبیاری اصلاحی بررسی شود.",
          "source_metric_type": "moisture",
          "timestamp": null,
          "payload": {}
        }
      ]
    }
  }
}
```

## خطاهای متداول

### مزرعه پیدا نشد

اگر `farm_uuid` متعلق به کاربر نباشد یا وجود نداشته باشد:

```json
{
  "farm_uuid": [
    "Farm not found."
  ]
}
```

### بدنه نامعتبر

اگر فیلدهای نامعتبر بفرستید:

```json
{
  "unexpected_field": [
    "This field is not allowed."
  ]
}
```

### احراز هویت نامعتبر

- در صورت نبود token یا نامعتبر بودن آن، پاسخ `401 Unauthorized` برمی‌گردد.

## توصیه برای فرانت

- برای هر alert یک `alert_id` پایدار بفرستید.
- اگر alert جدیدی ندارید، می‌توانید فقط `farm_uuid` بفرستید.
- از `headline` و `overview` برای summary UI استفاده کنید.
- از `notifications` برای notification list یا toast استفاده کنید.
- از `tracker.mostCriticalIssue` و `tracker.recommendedOperationalActions` برای CTA و نمایش اقدام فوری استفاده کنید.
