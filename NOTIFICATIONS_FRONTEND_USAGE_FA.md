# راهنمای استفاده فرانت از سیستم نوتیفیکیشن (SSE + Redis)

این سند روش اتصال فرانت به سیستم نوتیفیکیشن جدید را توضیح می‌دهد.

## 1) APIهای موجود

- استریم نوتیفیکیشن (SSE):
  - `GET /api/notifications/stream/?channel=<channel_name>`
- ارسال نوتیفیکیشن (برای تست/ادمین):
  - `POST /api/notifications/publish/`

هر دو endpoint نیازمند احراز هویت هستند.

## 2) فرمت پیام دریافتی در SSE

payload نمونه:

```json
{
  "id": "f6f5d6ca-54f1-4d0e-8d29-5ef5760a3b40",
  "event": "notification",
  "title": "آبیاری",
  "message": "زمان آبیاری مزرعه فرا رسیده است.",
  "level": "info",
  "metadata": {
    "farm_uuid": "11111111-1111-1111-1111-111111111111"
  },
  "created_at": "2026-04-03T20:00:00.000000+00:00"
}
```

`event` به‌صورت SSE event name هم ارسال می‌شود.

## 3) انتخاب channel

الگوی پیشنهادی:

- کانال کاربر: `user-<user_id>`
- کانال مزرعه: `farm-<farm_uuid>`

در وضعیت فعلی backend اگر `channel` نفرستید، پیش‌فرض روی `user-<current_user_id>` است.

## 4) اتصال در فرانت

نکته مهم: چون backend روی JWT (`Authorization: Bearer ...`) است، `EventSource` پیش‌فرض مرورگر امکان ارسال header سفارشی ندارد.  
پس یا از polyfill/library استفاده کنید، یا مکانیزم auth مبتنی بر cookie داشته باشید.

نمونه با `@microsoft/fetch-event-source`:

```js
import { fetchEventSource } from "@microsoft/fetch-event-source";

const API_BASE = "https://your-domain.com";
const token = localStorage.getItem("access_token");
const channel = "user-123";

await fetchEventSource(`${API_BASE}/api/notifications/stream/?channel=${channel}`, {
  method: "GET",
  headers: {
    Authorization: `Bearer ${token}`,
    Accept: "text/event-stream"
  },
  onopen(response) {
    if (!response.ok) throw new Error("SSE connection failed");
  },
  onmessage(event) {
    if (!event.data) return;
    const payload = JSON.parse(event.data);
    // نمایش toast / badge / in-app notification
    console.log("notification:", payload);
  },
  onerror(err) {
    console.error("SSE error", err);
    // کتابخانه به شکل پیش‌فرض reconnect می‌کند
  }
});
```

## 5) ارسال نوتیفیکیشن (برای تست از فرانت یا پنل ادمین)

درخواست:

```http
POST /api/notifications/publish/
Authorization: Bearer <access_token>
Content-Type: application/json
```

بدنه:

```json
{
  "channel": "user-123",
  "title": "نمونه نوتیف",
  "message": "این پیام تستی است",
  "level": "info",
  "event": "notification",
  "metadata": {
    "farm_uuid": "11111111-1111-1111-1111-111111111111"
  }
}
```

## 6) پیشنهاد UX در فرانت

- روی `level`، رنگ‌بندی toast انجام دهید (`info/success/warning/error`).
- `metadata` را برای deep-link استفاده کنید (مثلاً رفتن به صفحه مزرعه).
- هنگام logout، اتصال SSE را قطع کنید.
- هنگام تغییر کاربر یا مزرعه، channel را عوض کنید و اتصال قبلی را ببندید.

## 7) خطاهای رایج

- `401 Unauthorized`: توکن نامعتبر/منقضی شده.
- `403 Forbidden`: کاربر دسترسی لازم به endpoint ندارد.
- اتصال برقرار می‌شود ولی پیامی نمی‌آید: channel اشتباه است یا پیام روی channel دیگری publish شده است.
