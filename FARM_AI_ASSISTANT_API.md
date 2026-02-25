# مستندات APIهای دستیار هوشمند مزرعه (Farm AI Assistant)

این سند تمام APIهای مورد نیاز برای صفحه **Farm AI Assistant** را شرح می‌دهد: ورودی‌ها، خروجی‌ها و استفاده در UI.

**مسیر صفحه:** `(dashboard)/(private)/farm-ai-assistant`  
**کامپوننت اصلی:** `FarmAiAssistantChat`

---

## نمای کلی

دستیار هوشمند مزرعه برای کار به موارد زیر نیاز دارد:

| ردیف | API | هدف |
|------|-----|------|
| ۱ | **ارسال پیام به دستیار (Chat/Complete)** | دریافت پاسخ ساخت‌یافته (توصیه، لیست، هشدار) بر اساس پیام کاربر و زمینه مزرعه |
| ۲ | **دریافت زمینه مزرعه (Farm Context)** | پر کردن نوار «زمینه مزرعه» (نوع خاک، EC آب، محصول، مرحله رشد، آخرین آبیاری) |
| ۳ | **توصیه آبیاری** | در صورت درخواست کاربر یا تصمیم دستیار برای توصیه آبیاری |
| ۴ | **توصیه کوددهی** | در صورت درخواست کاربر یا توصیه کود |
| ۵ | **تشخیص آفت از تصویر** | وقتی کاربر تصویر گیاه را ارسال می‌کند |

---

## ۱. API ارسال پیام به دستیار (Farm AI Chat)

این API هسته اصلی دستیار است و در حال حاضر در فرانت با پاسخ دمو شبیه‌سازی شده است؛ باید با API واقعی جایگزین شود.

### ۱.۱ مشخصات

- **متد:** `POST`
- **آدرس پیشنهادی:** `POST /api/farm-ai-assistant/chat/` یا `POST /api/farm-ai-assistant/messages/`
- **هدف:** ارسال پیام کاربر (و در صورت وجود تصویر) به همراه زمینه مزرعه و دریافت پاسخ ساخت‌یافته دستیار.

### ۱.۲ ورودی (Request Body)

| فیلد | نوع | اجباری | توضیح |
|------|-----|--------|--------|
| `content` | string | بله | متن پیام کاربر |
| `images` | string[] یا base64[] | خیر | آرایه آدرس تصاویر یا داده base64 (در صورت استفاده از آپلود تصویر دوربین در چت) |
| `conversation_id` | string | خیر | شناسه مکالمه برای ادامه گفتگو؛ در اولین پیام ارسال نشود |
| `farm_context` | object | توصیه | زمینه مزرعه برای پاسخ شخصی‌سازی‌شده (در صورت نبودن، بک‌اند می‌تواند از پیش‌فرض استفاده کند) |

ساختار پیشنهادی `farm_context` (هم‌خوان با `FarmContext` در فرانت):

```json
{
  "content": "برنامه آبیاری برای گوجه در مرحله گلدهی چطور باشد؟",
  "farm_context": {
    "soilType": "Loamy",
    "waterEC": "1.2 dS/m",
    "selectedCrop": "Tomato",
    "growthStage": "Flowering",
    "lastIrrigationStatus": "2 days ago"
  }
}
```

اگر از **تصویر** استفاده شود (دکمه دوربین در input):

```json
{
  "content": "این برگ زرد شده، چه مشکلی داره؟",
  "images": ["data:image/jpeg;base64,..."],
  "farm_context": { ... }
}
```

### ۱.۳ خروجی (Response Body)

پاسخ باید شامل **بخش‌های ساخت‌یافته** (sections) باشد تا در UI به صورت کارت (توصیه، لیست، هشدار) رندر شود.

**قالب پیشنهادی:**

```json
{
  "status": "success",
  "data": {
    "message_id": "a-1739123456789",
    "conversation_id": "conv-abc123",
    "content": "",
    "sections": [
      {
        "type": "recommendation",
        "title": "Irrigation recommendation",
        "icon": "droplet",
        "frequency": "3 times per week",
        "amount": "15–20 L per plant",
        "timing": "Early morning (05:00–07:00)",
        "expandableExplanation": "Your loamy soil holds moisture well..."
      },
      {
        "type": "list",
        "title": "Key points",
        "icon": "leaf",
        "items": [
          "Avoid midday watering to reduce evaporation",
          "Drip irrigation preferred for root zone targeting"
        ]
      },
      {
        "type": "warning",
        "title": "Weather advisory",
        "icon": "warning",
        "content": "High temps forecasted next week. Consider increasing frequency."
      }
    ]
  }
}
```

**ساختار هر بخش (Section) مطابق `AIResponseSection` در فرانت:**

| فیلد | نوع | اجباری | توضیح |
|------|-----|--------|--------|
| `type` | string | بله | یکی از: `text` \| `list` \| `recommendation` \| `warning` |
| `title` | string | خیر | عنوان بخش |
| `content` | string | خیر | برای `type: "text"` یا `type: "warning"` |
| `items` | string[] | خیر | برای `type: "list"` |
| `icon` | string | خیر | یکی از: `droplet` \| `leaf` \| `warning` \| `fertilizer` \| `calendar` |
| `frequency` | string | خیر | فقط برای `recommendation`: تعداد دفعات (مثلاً در هفته) |
| `amount` | string | خیر | فقط برای `recommendation`: مقدار (مثلاً لیتر یا کیلوگرم) |
| `timing` | string | خیر | فقط برای `recommendation`: زمان پیشنهادی |
| `expandableExplanation` | string | خیر | فقط برای `recommendation`: توضیح قابل گسترش «چرا این توصیه» |

- اگر `content` خالی باشد و فقط `sections` برگردد، در UI فقط کارت‌ها نمایش داده می‌شوند (مطابق پیاده‌سازی فعلی).
- در صورت خطا انتظار می‌رود پاسخ با `status: "error"` و پیام مناسب برگردد.

---

## ۲. API دریافت زمینه مزرعه (Farm Context)

برای پر کردن نوار «زمینه مزرعه» در بالای چت (نوع خاک، EC آب، محصول انتخاب‌شده، مرحله رشد، آخرین آبیاری).

- **وضعیت:** در بک‌اند فعلی endpoint اختصاصی برای «یک جا گرفتن» زمینه مزرعه وجود ندارد.
- **راه‌حل فعلی:** فرانت می‌تواند داده را از منابع موجود جمع کند:
  - **توصیه آبیاری:** `GET /api/irrigation-recommendation/config/` → `farmInfo` (soilType, waterQuality, climateZone) و `cropOptions`
  - **توصیه کوددهی:** `GET /api/fertilization-recommendation/config/` → `farmData` (soilType, organicMatter, waterEC)، `growthStages`، `cropOptions`
- **پیشنهاد برای آینده:** یک endpoint مثل `GET /api/farm-ai-assistant/context/` یا `GET /api/farm-dashboard-config/...` که یک آبجکت هم‌خوان با `FarmContext` فرانت برگرداند (مثلاً `soilType`, `waterEC`, `selectedCrop`, `growthStage`, `lastIrrigationStatus`).

---

## ۳. API توصیه آبیاری

وقتی کاربر در چت درخواست توصیه آبیاری می‌کند (یا دستیار تصمیم می‌گیرد توصیه آبیاری بدهد)، می‌توان از API موجود استفاده کرد.

- **Config (برای فرم/گزینه‌ها):** `GET /api/irrigation-recommendation/config/`
- **توصیه (برنامه آبیاری):** `POST /api/irrigation-recommendation/recommend/`

ورودی پیشنهادی برای `recommend`: `crop_id`, `soilType`, `waterQuality`, `climateZone` (در نسخه فعلی mock است و در پاسخ استفاده نمی‌شود).

جزئیات و نمونه پاسخ: [RECOMMENDATION_APIS.md](./RECOMMENDATION_APIS.md#۱-توصیه-آبیاری-irrigation-recommendation).

---

## ۴. API توصیه کوددهی

در صورت درخواست کاربر برای توصیه کود یا تصمیم دستیار برای دادن توصیه کود.

- **Config:** `GET /api/fertilization-recommendation/config/`
- **توصیه:** `POST /api/fertilization-recommendation/recommend/`

ورودی پیشنهادی برای `recommend`: `crop_id`, `growth_stage`, `soilType`, `organicMatter`, `waterEC` (در نسخه فعلی mock است).

جزئیات و نمونه پاسخ: [RECOMMENDATION_APIS.md](./RECOMMENDATION_APIS.md#۳-توصیه-کوددهی-fertilization-recommendation).

---

## ۵. API تشخیص آفت از تصویر

وقتی کاربر در چت تصویر گیاه را ارسال می‌کند (دکمه دوربین یا آپلود).

- **تحلیل تصویر:** `POST /api/pest-detection/analyze/`
- **ورودی:** بدن درخواست می‌تواند شامل تصویر (مثلاً form-data با فایل یا JSON با base64) باشد. در نسخه فعلی پاسخ ثابت (mock) است.
- **خروجی:** `pest`, `confidence`, `description`, `treatment`

جزئیات و نمونه پاسخ: [RECOMMENDATION_APIS.md](./RECOMMENDATION_APIS.md#۲-تشخیص-آفت-pest-detection).

---

## خلاصه Endpointها برای Farm AI Assistant

| ردیف | API | متد | Endpoint | وضعیت |
|------|-----|------|----------|--------|
| ۱ | Farm AI Chat | POST | `/api/farm-ai-assistant/chat/` (پیشنهادی) | **پیاده‌سازی نشده** |
| ۲ | Farm Context | GET | `/api/farm-ai-assistant/context/` (پیشنهادی) | **پیاده‌سازی نشده**؛ استفاده از configهای آبیاری/کوددهی |
| ۳ | توصیه آبیاری | GET | `/api/irrigation-recommendation/config/` | موجود (mock) |
| ۳ | توصیه آبیاری | POST | `/api/irrigation-recommendation/recommend/` | موجود (mock) |
| ۴ | توصیه کوددهی | GET | `/api/fertilization-recommendation/config/` | موجود (mock) |
| ۴ | توصیه کوددهی | POST | `/api/fertilization-recommendation/recommend/` | موجود (mock) |
| ۵ | تشخیص آفت | POST | `/api/pest-detection/analyze/` | موجود (mock) |
