# مستند نحوه ارتباط با سرویس `farm_ai_assistant`

این فایل برای تیم بک‌اند تهیه شده و صرفاً بر اساس مسیرهای فعال در `farm_ai_assistant/urls.py` و رفتار فعلی ویوها نوشته شده است.

## Base URL

تمام endpointهای این سرویس با prefix زیر در دسترس هستند:

```text
/api/farm-ai-assistant/
```

نمونه کامل:

```text
https://<domain>/api/farm-ai-assistant/
```

## احراز هویت

تمام endpointهای عملیاتی این ماژول نیاز به احراز هویت دارند:

- نوع دسترسی: `IsAuthenticated`
- هدر موردنیاز:

```http
Authorization: Bearer <access_token>
```

> اگر کاربر لاگین نباشد، درخواست با خطای احراز هویت رد می‌شود.

## وضعیت endpointها

### endpointهای فعال در `farm_ai_assistant/urls.py`

| Method | Endpoint | کاربرد |
|---|---|---|
| `GET` | `/context/` | دریافت context نمایشی/پیش‌فرض برای UI |
| `POST` | `/chat/task/` | ثبت پیام کاربر و ساخت task در سرویس AI |
| `GET` | `/chat/task/<task_id>/status/` | بررسی وضعیت task و دریافت نتیجه نهایی |
| `GET` | `/chats/` | لیست گفتگوهای کاربر |
| `POST` | `/chats/` | ایجاد conversation خالی |
| `DELETE` | `/chats/<conversation_id>/` | حذف conversation |
| `GET` | `/chats/<conversation_id>/messages/` | دریافت پیام‌های یک conversation |

### endpoint غیرفعال

endpoint زیر در فایل `urls.py` کامنت شده و در حال حاضر قابل استفاده نیست:

```text
POST /api/farm-ai-assistant/chat/
```

یعنی در وضعیت فعلی، جریان اصلی ارتباط با AI به شکل **asynchronous task-based** پیاده‌سازی شده است.

---

## 1) دریافت context

### Request

```http
GET /api/farm-ai-assistant/context/
Authorization: Bearer <token>
```

### Response

```json
{
  "status": "success",
  "data": {
    "...": "context mock/initial data"
  }
}
```

### توضیح

- این endpoint فعلاً داده context را از `mock_data` برمی‌گرداند.
- برای preload کردن اطلاعات اولیه UI مناسب است.
- این endpoint به سرویس خارجی AI کال نمی‌زند.

---

## 2) ایجاد task برای ارسال پیام به AI

این endpoint مهم‌ترین مسیر ارتباطی با سرویس AI است.

### Request

```http
POST /api/farm-ai-assistant/chat/task/
Authorization: Bearer <token>
Content-Type: application/json
```

### Body

```json
{
  "content": "برای گوجه در مرحله گلدهی برنامه آبیاری بده",
  "images": [],
  "conversation_id": "optional-uuid",
  "title": "optional title",
  "farm_context": {
    "soilType": "Loamy",
    "waterEC": "1.2 dS/m",
    "selectedCrop": "Tomato",
    "growthStage": "Flowering"
  }
}
```

### فیلدها

| فیلد | نوع | اجباری | توضیح |
|---|---|---|---|
| `content` | `string` | اختیاری* | متن پیام کاربر |
| `images` | `string[]` | اختیاری | لیست URL/base64 تصویر |
| `conversation_id` | `uuid` | اختیاری | اگر گفتگو از قبل وجود دارد |
| `title` | `string` | اختیاری | عنوان گفتگو |
| `farm_context` | `object` | اختیاری | context مزرعه |

> حداقل یکی از `content` یا `images` باید ارسال شود. در غیر این صورت validation error برمی‌گردد.

### رفتار بک‌اند داخلی

در این endpoint این اتفاق‌ها می‌افتد:

1. اگر `conversation_id` ارسال شده باشد، همان conversation متعلق به همان کاربر لود می‌شود.
2. اگر `conversation_id` ارسال نشده باشد، یک conversation جدید ساخته می‌شود.
3. یک message با `role=user` در دیتابیس ذخیره می‌شود.
4. سپس بک‌اند به سرویس خارجی AI درخواست می‌زند.

### payload ارسالی به سرویس خارجی AI

بک‌اند این payload را به سرویس خارجی ارسال می‌کند:

```json
{
  "content": "...",
  "query": "...",
  "images": [],
  "conversation_id": "conversation-uuid",
  "user_id": 123,
  "farm_context": {},
  "title": "..."
}
```

### مسیر سرویس خارجی AI

```text
POST /rag/chat/generate
```

### Response موفق

```json
{
  "status": "success",
  "data": {
    "task_id": "abc123",
    "status": "PENDING",
    "status_url": "/tasks/abc123/status",
    "conversation_id": "4b9f4d2f-2e5f-4f7a-ae24-6e7fd9c3e0f1",
    "message_id": "5d3f7a8c-9f2e-4d0a-b56f-1f2c2f9c1a22"
  }
}
```

### کدهای وضعیت محتمل

| Status Code | معنی |
|---|---|
| `202` | task ساخته شده و باید polling انجام شود |
| `4xx/5xx` | خطای دریافتی از سرویس خارجی |
| `503` | سرویس خارجی AI در دسترس نیست |

---

## 3) بررسی وضعیت task

فرانت یا سرویس مصرف‌کننده باید با `task_id` وضعیت را poll کند.

### Request

```http
GET /api/farm-ai-assistant/chat/task/<task_id>/status/
Authorization: Bearer <token>
```

### مسیر سرویس خارجی AI

بک‌اند این درخواست را به سرویس خارجی پاس می‌دهد:

```text
GET /tasks/<task_id>/status
```

### Response در حالت در حال پردازش

```json
{
  "status": "success",
  "data": {
    "task_id": "abc123",
    "status": "PENDING",
    "conversation_id": "4b9f4d2f-2e5f-4f7a-ae24-6e7fd9c3e0f1",
    "progress": {
      "message": "Processing request"
    }
  }
}
```

### Response در حالت موفق

```json
{
  "status": "success",
  "data": {
    "task_id": "abc123",
    "status": "SUCCESS",
    "conversation_id": "4b9f4d2f-2e5f-4f7a-ae24-6e7fd9c3e0f1",
    "result": {
      "message_id": "9f3f8f61-cc71-4f70-a650-2f4dc6f4e5c2",
      "conversation_id": "4b9f4d2f-2e5f-4f7a-ae24-6e7fd9c3e0f1",
      "content": "پیشنهاد آبیاری شما آماده است",
      "sections": [
        {
          "type": "recommendation",
          "title": "Irrigation recommendation",
          "icon": "droplet",
          "frequency": "3 times per week",
          "amount": "15–20 L per plant",
          "timing": "Early morning",
          "expandableExplanation": "..."
        }
      ]
    }
  }
}
```

### Response در حالت خطا

```json
{
  "status": "success",
  "data": {
    "task_id": "abc123",
    "status": "FAILURE",
    "conversation_id": "4b9f4d2f-2e5f-4f7a-ae24-6e7fd9c3e0f1",
    "error": "something went wrong"
  }
}
```

### نکته مهم

اگر `status=SUCCESS` باشد و `result` از سرویس خارجی دریافت شود:

- نتیجه نهایی به message دستیار تبدیل و در دیتابیس ذخیره می‌شود.
- یک `assistant message` داخل همان conversation ساخته یا به‌روزرسانی می‌شود.
- خروجی `result` در پاسخ API به فرم نهایی UI normalize می‌شود.

---

## 4) لیست گفتگوها

### Request

```http
GET /api/farm-ai-assistant/chats/
Authorization: Bearer <token>
```

### Response

```json
{
  "status": "success",
  "data": [
    {
      "id": "4b9f4d2f-2e5f-4f7a-ae24-6e7fd9c3e0f1",
      "message_count": 4
    }
  ]
}
```

### توضیح

- فقط conversationهای متعلق به همان کاربر لاگین‌شده برگردانده می‌شود.
- مرتب‌سازی بر اساس `updated_at desc` و سپس `created_at desc` است.

---

## 5) ایجاد conversation خالی

### Request

```http
POST /api/farm-ai-assistant/chats/
Authorization: Bearer <token>
Content-Type: application/json
```

### Body

```json
{
  "title": "مشاوره آبیاری",
  "farm_context": {
    "soilType": "Loamy"
  }
}
```

### Response

```json
{
  "status": "success",
  "data": {
    "id": "4b9f4d2f-2e5f-4f7a-ae24-6e7fd9c3e0f1",
    "message_count": 0
  }
}
```

### کد وضعیت

```text
201 Created
```

---

## 6) دریافت پیام‌های یک conversation

### Request

```http
GET /api/farm-ai-assistant/chats/<conversation_id>/messages/
Authorization: Bearer <token>
```

### Response

```json
{
  "status": "success",
  "data": {
    "conversation_id": "4b9f4d2f-2e5f-4f7a-ae24-6e7fd9c3e0f1",
    "messages": [
      {
        "message_id": "11111111-1111-1111-1111-111111111111",
        "conversation_id": "4b9f4d2f-2e5f-4f7a-ae24-6e7fd9c3e0f1",
        "role": "user",
        "content": "برای گوجه آبیاری پیشنهاد بده",
        "sections": [],
        "images": [],
        "created_at": "2025-03-27T12:00:00Z"
      },
      {
        "message_id": "22222222-2222-2222-2222-222222222222",
        "conversation_id": "4b9f4d2f-2e5f-4f7a-ae24-6e7fd9c3e0f1",
        "role": "assistant",
        "content": "",
        "sections": [
          {
            "type": "list",
            "title": "Key points",
            "items": [
              "Avoid midday watering",
              "Use drip irrigation"
            ]
          }
        ],
        "images": [],
        "created_at": "2025-03-27T12:00:05Z"
      }
    ]
  }
}
```

### توضیح

- `role` یکی از دو مقدار `user` یا `assistant` است.
- برای messageهای `assistant`، فیلد `sections` می‌تواند پر باشد.
- برای messageهای `user`، معمولاً `sections` خالی است.

---

## 7) حذف conversation

### Request

```http
DELETE /api/farm-ai-assistant/chats/<conversation_id>/
Authorization: Bearer <token>
```

### Response

```json
{
  "status": "success",
  "data": {
    "conversation_id": "4b9f4d2f-2e5f-4f7a-ae24-6e7fd9c3e0f1"
  }
}
```

---

## فرمت `sections` در پاسخ نهایی AI

بخش `sections` برای render شدن خروجی دستیار در UI استفاده می‌شود.

### ساختار هر section

```json
{
  "type": "recommendation",
  "title": "Irrigation recommendation",
  "content": "",
  "items": [],
  "icon": "droplet",
  "frequency": "3 times per week",
  "amount": "15–20 L per plant",
  "timing": "Early morning",
  "expandableExplanation": "..."
}
```

### مقادیر مجاز `type`

- `text`
- `list`
- `recommendation`
- `warning`

### نکات نرمال‌سازی

بک‌اند فقط این کلیدها را از پاسخ AI نگه می‌دارد:

- `type`
- `title`
- `content`
- `items`
- `icon`
- `frequency`
- `amount`
- `timing`
- `expandableExplanation`

اگر سرویس خارجی فیلد اضافی برگرداند، در response نهایی حذف می‌شود.

---

## قواعد مهم کسب‌وکاری/فنی

### مالکیت conversation

- هر conversation فقط برای owner خودش قابل مشاهده/حذف/دریافت پیام است.
- اگر `conversation_id` مربوط به کاربر دیگری باشد، `404 Conversation not found` برمی‌گردد.

### title conversation

- اگر conversation جدید بدون title ساخته شود:
  - در endpoint `POST /chats/` عنوان پیش‌فرض `New chat` است.
  - در endpoint `POST /chat/task/` اگر title داده نشود، از ابتدای `content` یا fallback پیش‌فرض استفاده می‌شود.

### ذخیره‌سازی پیام‌ها

- پیام کاربر قبل از تماس با AI ذخیره می‌شود.
- پاسخ دستیار بعد از اتمام task ذخیره می‌شود.
- داده خام/کمکی در `raw_response` نگهداری می‌شود.

### تصاویر

- فیلد `images` آرایه‌ای از string است.
- این string می‌تواند URL، path یا base64 باشد؛ validation فعلی فقط نوع string را چک می‌کند.

---

## فلو پیشنهادی برای استفاده از API

### سناریوی استاندارد چت

1. فرانت در صورت نیاز `GET /context/` را صدا می‌زند.
2. فرانت پیام کاربر را با `POST /chat/task/` ارسال می‌کند.
3. از پاسخ، `task_id` و `conversation_id` دریافت می‌شود.
4. فرانت هر چند ثانیه `GET /chat/task/<task_id>/status/` را poll می‌کند.
5. وقتی `status=SUCCESS` شد، نتیجه نهایی از `result` خوانده می‌شود.
6. برای history کامل، `GET /chats/<conversation_id>/messages/` فراخوانی می‌شود.

---

## نمونه cURL

### ارسال پیام و ساخت task

```bash
curl -X POST 'https://<domain>/api/farm-ai-assistant/chat/task/' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "content": "برای خیار گلخانه‌ای برنامه آبیاری بده",
    "farm_context": {
      "soilType": "Sandy Loam",
      "selectedCrop": "Cucumber",
      "growthStage": "Flowering"
    }
  }'
```

### بررسی وضعیت task

```bash
curl -X GET 'https://<domain>/api/farm-ai-assistant/chat/task/abc123/status/' \
  -H 'Authorization: Bearer <token>'
```

### دریافت پیام‌های گفتگو

```bash
curl -X GET 'https://<domain>/api/farm-ai-assistant/chats/4b9f4d2f-2e5f-4f7a-ae24-6e7fd9c3e0f1/messages/' \
  -H 'Authorization: Bearer <token>'
```

---

## جمع‌بندی سریع برای تیم backend

- endpoint sync chat فعلاً فعال نیست.
- endpoint اصلی برای ارتباط با AI برابر `POST /chat/task/` است.
- نتیجه از طریق `GET /chat/task/<task_id>/status/` گرفته می‌شود.
- conversation و messageها داخل دیتابیس داخلی ذخیره می‌شوند.
- همه endpointها نیازمند authentication هستند.
- ساختار خروجی نهایی باید با `sections` برای UI سازگار باشد.
