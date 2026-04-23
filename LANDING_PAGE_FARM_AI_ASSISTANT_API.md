# راهنمای اتصال Landing Page به Farm AI Assistant و Auth API

این فایل برای تیم فرانت/لندینگ نوشته شده تا بتوانند از داخل Docker Network به بک‌اند وصل شوند و APIهای احراز هویت و Farm AI Assistant را مصرف کنند.

## 1) اتصال از طریق Docker Network

بک‌اند در `docker-compose.yaml` روی network خارجی `crop_network` اجرا می‌شود و سرویس وب آن:

- service name: `web`
- container name: `backend-web`
- internal port: `8000`

### نکته مهم

اگر فرانت هم داخل Docker اجرا می‌شود، از داخل کانتینر نباید از `localhost:8000` استفاده کنید، چون `localhost` به همان کانتینر فرانت اشاره می‌کند، نه به بک‌اند.

### آدرس پیشنهادی برای اتصال داخل Docker Network

```text
http://backend-web:8000
```

در بسیاری از موارد `http://web:8000` هم کار می‌کند، اما چون `container_name` به‌صورت صریح `backend-web` تعریف شده، برای اتصال بین دو سرویس روی `crop_network` بهتر است از همین آدرس استفاده شود.

### اگر network هنوز ساخته نشده است

```bash
docker network create crop_network
```

### نمونه اتصال سرویس فرانت به همان network

```yaml
services:
  landing:
    build: .
    container_name: landing-web
    environment:
      BACKEND_BASE_URL: http://backend-web:8000
    networks:
      - crop_network

networks:
  crop_network:
    external: true
```

### پیشنهاد برای env فرانت

```env
BACKEND_BASE_URL=http://backend-web:8000
```

### اگر درخواست از خود مرورگر کاربر ارسال می‌شود

اگر فرانت در مرورگر API را مستقیم صدا می‌زند، معمولاً باید از آدرس host-mapped استفاده کنید:

```text
http://localhost:8000
```

اما اگر درخواست از سمت سرور فرانت/SSR/Nuxt/Next داخل کانتینر ارسال می‌شود، از این آدرس استفاده کنید:

```text
http://backend-web:8000
```

---

## 2) Base URL

### برای ارتباط container-to-container

```text
http://backend-web:8000
```

### Prefixهای موردنیاز

- Auth: `/api/auth/`
- Farm AI Assistant: `/api/farm-ai-assistant/`

---

## 3) جریان کلی برای Landing Page

برای چت landing page، ارسال `farm_uuid` الزامی نیست.

یعنی اگر کاربر داخل landing page پیام بدهد:

- فقط کافی است کاربر لاگین باشد
- `farm_uuid` را ارسال نکنید
- سیستم conversation را به‌صورت landing conversation با `farm = null` ذخیره می‌کند
- در responseها معمولاً `farm_uuid` برابر `null` خواهد بود

### فلو پیشنهادی

1. کاربر با `register` یا `login` توکن بگیرد.
2. توکن را در هدر `Authorization: Bearer <token>` بفرستید.
3. برای شروع چت landing از `POST /api/farm-ai-assistant/chat/task/` بدون `farm_uuid` استفاده کنید.
4. `task_id` و `conversation_id` را از پاسخ نگه دارید.
5. با `GET /api/farm-ai-assistant/chat/task/{task_id}/status/` وضعیت را poll کنید.
6. برای history از `GET /api/farm-ai-assistant/chats/{conversation_id}/messages/` استفاده کنید.
7. برای لیست چت‌های landing از `GET /api/farm-ai-assistant/chats/` بدون `farm_uuid` استفاده کنید.

---

## 4) Authentication APIs

## 4.1) Register

- Method: `POST`
- URL: `/api/auth/register/`
- Auth: نیاز ندارد

### Request

```json
{
  "username": "landing_user",
  "email": "landing@example.com",
  "phone_number": "09120000000",
  "password": "secret123",
  "first_name": "Landing",
  "last_name": "User"
}
```

### Response 201

```json
{
  "code": 201,
  "msg": "success",
  "data": {
    "id": 1,
    "username": "landing_user",
    "email": "landing@example.com",
    "first_name": "Landing",
    "last_name": "User",
    "phone_number": "09120000000"
  },
  "token": "<access_token>"
}
```

### خطاهای رایج

- `400`: username تکراری
- `400`: email تکراری
- `400`: phone_number تکراری

---

## 4.2) Login

- Method: `POST`
- URL: `/api/auth/login/`
- Auth: نیاز ندارد

### Request

`identifier` می‌تواند `username` یا `email` یا `phone_number` باشد.

```json
{
  "identifier": "landing_user",
  "password": "secret123"
}
```

### Response 200

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "id": 1,
    "username": "landing_user",
    "email": "landing@example.com",
    "first_name": "Landing",
    "last_name": "User",
    "phone_number": "09120000000"
  },
  "token": "<access_token>"
}
```

### خطای رایج

```json
{
  "code": 401,
  "msg": "Invalid credentials."
}
```

---

## 5) هدر احراز هویت برای Farm AI Assistant

تمام endpointهای Farm AI Assistant نیاز به لاگین دارند:

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

---

## 6) Farm AI Assistant APIs

## 6.1) ارسال پیام و ساخت task

- Method: `POST`
- URL: `/api/farm-ai-assistant/chat/task/`
- Auth: لازم است
- برای landing page: `farm_uuid` را ارسال نکنید

### Request نمونه برای landing

```json
{
  "content": "برای شروع کشاورزی چه محصولی مناسب‌تر است؟",
  "images": [],
  "title": "Landing chat",
  "farm_context": {
    "source": "landing",
    "page": "home"
  }
}
```

### Request با ادامه conversation قبلی

```json
{
  "conversation_id": "4b9f4d2f-2e5f-4f7a-ae24-6e7fd9c3e0f1",
  "content": "برای منطقه کم‌آب چه پیشنهادی داری؟",
  "images": []
}
```

### فیلدها

| فیلد | نوع | اجباری | توضیح |
|---|---|---|---|
| `farm_uuid` | `uuid` | خیر | برای landing ارسال نشود |
| `content` | `string` | اختیاری* | متن پیام |
| `images` | `string[]` | اختیاری | لیست URL/base64/path |
| `conversation_id` | `uuid` | اختیاری | ادامه چت قبلی |
| `title` | `string` | اختیاری | عنوان چت جدید |
| `farm_context` | `object` | اختیاری | context اضافی UI |

`*` حداقل یکی از `content` یا `images` باید ارسال شود.

### Response 202

```json
{
  "status": "success",
  "data": {
    "task_id": "farm-ai-chat-task-123",
    "status": "PENDING",
    "status_url": "/api/tasks/farm-ai-chat-task-123/status/",
    "conversation_id": "4b9f4d2f-2e5f-4f7a-ae24-6e7fd9c3e0f1",
    "message_id": "5d3f7a8c-9f2e-4d0a-b56f-1f2c2f9c1a22",
    "farm_uuid": null
  }
}
```

### خطاهای رایج

- `400`: اگر نه `content` باشد نه `images`
- `404`: اگر `conversation_id` متعلق به کاربر نباشد
- `503`: اگر سرویس خارجی AI در دسترس نباشد

---

## 6.2) بررسی وضعیت task

- Method: `GET`
- URL: `/api/farm-ai-assistant/chat/task/{task_id}/status/`
- Auth: لازم است
- برای landing page: بدون `farm_uuid`

### Request

```http
GET /api/farm-ai-assistant/chat/task/farm-ai-chat-task-123/status/
Authorization: Bearer <access_token>
```

### Response در حالت pending

```json
{
  "status": "success",
  "data": {
    "task_id": "farm-ai-chat-task-123",
    "status": "PENDING",
    "conversation_id": "4b9f4d2f-2e5f-4f7a-ae24-6e7fd9c3e0f1",
    "farm_uuid": null,
    "progress": {
      "message": "Processing request"
    }
  }
}
```

### Response در حالت success

```json
{
  "status": "success",
  "data": {
    "task_id": "farm-ai-chat-task-123",
    "status": "SUCCESS",
    "conversation_id": "4b9f4d2f-2e5f-4f7a-ae24-6e7fd9c3e0f1",
    "farm_uuid": null,
    "result": {
      "message_id": "9f3f8f61-cc71-4f70-a650-2f4dc6f4e5c2",
      "conversation_id": "4b9f4d2f-2e5f-4f7a-ae24-6e7fd9c3e0f1",
      "farm_uuid": null,
      "task_id": "farm-ai-chat-task-123",
      "content": "Here is the recommended plan.",
      "sections": [
        {
          "type": "recommendation",
          "title": "Irrigation Plan",
          "icon": "droplet",
          "frequency": "3 times per week",
          "amount": "15 liters per plant",
          "timing": "Early morning",
          "expandableExplanation": "Loamy soil holds moisture well, so moderate frequency is enough."
        }
      ]
    }
  }
}
```

### Response در حالت failure

```json
{
  "status": "success",
  "data": {
    "task_id": "farm-ai-chat-task-123",
    "status": "FAILURE",
    "conversation_id": "4b9f4d2f-2e5f-4f7a-ae24-6e7fd9c3e0f1",
    "farm_uuid": null,
    "error": "something went wrong"
  }
}
```

### پیشنهاد برای polling

- هر `2` تا `3` ثانیه یک بار status را چک کنید
- وقتی `status` برابر `SUCCESS` یا `FAILURE` شد polling را متوقف کنید

---

## 6.3) دریافت لیست chatها

- Method: `GET`
- URL: `/api/farm-ai-assistant/chats/`
- Auth: لازم است
- برای landing page: بدون `farm_uuid`

### رفتار

اگر `farm_uuid` ارسال نشود:

- فقط conversationهای landing همان کاربر برمی‌گردند
- یعنی فقط رکوردهایی که مزرعه ندارند

### Request

```http
GET /api/farm-ai-assistant/chats/
Authorization: Bearer <access_token>
```

### Response 200

```json
{
  "status": "success",
  "data": [
    {
      "id": "4b9f4d2f-2e5f-4f7a-ae24-6e7fd9c3e0f1",
      "farm_uuid": null,
      "message_count": 4
    }
  ]
}
```

---

## 6.4) ساخت conversation خالی

- Method: `POST`
- URL: `/api/farm-ai-assistant/chats/`
- Auth: لازم است
- برای landing page: بدون `farm_uuid`

### Request

```json
{
  "title": "مشاوره اولیه",
  "farm_context": {
    "source": "landing"
  }
}
```

### Response 201

```json
{
  "status": "success",
  "data": {
    "id": "4b9f4d2f-2e5f-4f7a-ae24-6e7fd9c3e0f1",
    "farm_uuid": null,
    "message_count": 0
  }
}
```

---

## 6.5) حذف conversation

- Method: `DELETE`
- URL: `/api/farm-ai-assistant/chats/{conversation_id}/`
- Auth: لازم است
- برای landing page: بدون `farm_uuid`

### رفتار

اگر `farm_uuid` نفرستید، فقط conversationهای landing همان کاربر قابل حذف هستند.

### Request

```http
DELETE /api/farm-ai-assistant/chats/4b9f4d2f-2e5f-4f7a-ae24-6e7fd9c3e0f1/
Authorization: Bearer <access_token>
```

### Response 200

```json
{
  "status": "success",
  "data": {
    "conversation_id": "4b9f4d2f-2e5f-4f7a-ae24-6e7fd9c3e0f1",
    "farm_uuid": null
  }
}
```

---

## 6.6) دریافت پیام‌های یک conversation

- Method: `GET`
- URL: `/api/farm-ai-assistant/chats/{conversation_id}/messages/`
- Auth: لازم است
- برای landing page: بدون `farm_uuid`

### رفتار

اگر `farm_uuid` ارسال نشود، فقط conversationهای landing همان کاربر لود می‌شوند.

### Request

```http
GET /api/farm-ai-assistant/chats/4b9f4d2f-2e5f-4f7a-ae24-6e7fd9c3e0f1/messages/
Authorization: Bearer <access_token>
```

### Response 200

```json
{
  "status": "success",
  "data": {
    "conversation_id": "4b9f4d2f-2e5f-4f7a-ae24-6e7fd9c3e0f1",
    "farm_uuid": null,
    "messages": [
      {
        "message_id": "11111111-1111-1111-1111-111111111111",
        "conversation_id": "4b9f4d2f-2e5f-4f7a-ae24-6e7fd9c3e0f1",
        "farm_uuid": null,
        "role": "user",
        "content": "برای شروع کشاورزی چه چیزی پیشنهاد می‌کنی؟",
        "sections": [],
        "images": [],
        "created_at": "2025-03-27T12:00:00Z"
      },
      {
        "message_id": "22222222-2222-2222-2222-222222222222",
        "conversation_id": "4b9f4d2f-2e5f-4f7a-ae24-6e7fd9c3e0f1",
        "farm_uuid": null,
        "role": "assistant",
        "content": "Here is the recommended plan.",
        "sections": [
          {
            "type": "list",
            "title": "Important Notes",
            "items": [
              "Avoid watering at noon",
              "Check leaf stress every two days"
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

---

## 7) مثال کامل فرانت برای Landing Chat

## 7.1) Register

```bash
curl -X POST 'http://backend-web:8000/api/auth/register/' \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "landing_user",
    "email": "landing@example.com",
    "phone_number": "09120000000",
    "password": "secret123",
    "first_name": "Landing",
    "last_name": "User"
  }'
```

## 7.2) Login

```bash
curl -X POST 'http://backend-web:8000/api/auth/login/' \
  -H 'Content-Type: application/json' \
  -d '{
    "identifier": "landing_user",
    "password": "secret123"
  }'
```

## 7.3) Create task

```bash
curl -X POST 'http://backend-web:8000/api/farm-ai-assistant/chat/task/' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "content": "برای شروع کشاورزی چه محصولی مناسب است؟",
    "farm_context": {
      "source": "landing",
      "page": "home"
    }
  }'
```

## 7.4) Poll task status

```bash
curl -X GET 'http://backend-web:8000/api/farm-ai-assistant/chat/task/farm-ai-chat-task-123/status/' \
  -H 'Authorization: Bearer <token>'
```

## 7.5) Get chat list

```bash
curl -X GET 'http://backend-web:8000/api/farm-ai-assistant/chats/' \
  -H 'Authorization: Bearer <token>'
```

## 7.6) Get messages

```bash
curl -X GET 'http://backend-web:8000/api/farm-ai-assistant/chats/4b9f4d2f-2e5f-4f7a-ae24-6e7fd9c3e0f1/messages/' \
  -H 'Authorization: Bearer <token>'
```

## 7.7) Delete conversation

```bash
curl -X DELETE 'http://backend-web:8000/api/farm-ai-assistant/chats/4b9f4d2f-2e5f-4f7a-ae24-6e7fd9c3e0f1/' \
  -H 'Authorization: Bearer <token>'
```

---

## 8) رفتار `farm_uuid` در Landing Page

برای endpointهای زیر در landing page لازم نیست `farm_uuid` ارسال شود:

- `POST /api/farm-ai-assistant/chat/task/`
- `GET /api/farm-ai-assistant/chat/task/{task_id}/status/`
- `GET /api/farm-ai-assistant/chats/`
- `POST /api/farm-ai-assistant/chats/`
- `DELETE /api/farm-ai-assistant/chats/{conversation_id}/`
- `GET /api/farm-ai-assistant/chats/{conversation_id}/messages/`

### نتیجه این رفتار

- چت به کاربر وابسته است
- چت به مزرعه خاصی وابسته نیست
- در response مقدار `farm_uuid` معمولاً `null` است

---

## 9) چیزی که فرانت باید نگه دارد

بعد از login این موارد را در state یا storage نگه دارید:

- `token`
- `user`

بعد از `POST /chat/task/` این موارد را نگه دارید:

- `conversation_id`
- `task_id`
- `message_id`

برای ادامه chat:

- `conversation_id` را در درخواست بعدی دوباره بفرستید

---

## 10) نکات نهایی

- تمام APIهای Farm AI Assistant به توکن نیاز دارند.
- برای landing page، `farm_uuid` را نفرستید.
- اگر فرانت داخل Docker است، آدرس بک‌اند را `http://backend-web:8000` بگذارید.
- اگر فرانت از داخل browser مستقیم درخواست می‌زند، معمولاً `http://localhost:8000` لازم است.
- `localhost` داخل کانتینر فرانت، آدرس بک‌اند نیست.

