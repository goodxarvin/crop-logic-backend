# مستندات API های صفحات منوی عمودی

این مستندات شامل تمام API های مورد نیاز برای صفحات موجود در VerticalMenu است.

**توجهات مهم:**
- صفحات User Management و Roles & Permissions فقط برای ادمین قابل دسترسی است
- صفحات Calendar، Kanban، و Todo باید به یکدیگر متصل باشند و تسک‌های غیرروتین در هر سه قابل نمایش باشند
- AI Chat باید به تسک‌های Calendar، Kanban، و Todo دسترسی داشته باشد
- AI Chat باید نسبت به برخی پیام‌ها حساس باشد (sensitive message handling)
- سیستم Authentication جزو این مستندات نیست

---

## فهرست مطالب

1. [Chat](#1-chat)
2. [AI Chat](#2-ai-chat)
3. [Calendar](#3-calendar)
4. [Kanban](#4-kanban)
5. [Todo](#5-todo)
6. [User Management](#6-user-management)
7. [Roles & Permissions](#7-roles--permissions)
8. [Sensor Hub](#8-sensor-hub)

---

## 1. Chat

**Route:** `/apps/chat`

**دسترسی:** همه کاربران

### API های مورد نیاز

#### 1.1. دریافت لیست مخاطبین

**Endpoint:** `GET /api/chat/contacts`

**Response:**
```json
{
  "contacts": [
    {
      "id": number,
      "fullName": "string",
      "role": "string",
      "about": "string",
      "avatar": "string",
      "avatarColor": "primary" | "success" | "error" | "warning" | "info",
      "status": "busy" | "away" | "online" | "offline"
    }
  ]
}
```

**توضیحات فیلدها:**

| فیلد | نوع | توضیحات |
|------|-----|---------|
| `contacts[].id` | number | شناسه یکتا مخاطب |
| `contacts[].fullName` | string | نام کامل |
| `contacts[].role` | string | نقش کاربر |
| `contacts[].about` | string | درباره کاربر |
| `contacts[].avatar` | string | آواتار (URL) |
| `contacts[].avatarColor` | ThemeColor | رنگ آواتار (در صورت نبودن تصویر) |
| `contacts[].status` | StatusType | وضعیت آنلاین/آفلاین |

#### 1.2. دریافت چت‌های کاربر

**Endpoint:** `GET /api/chat/conversations`

**Response:**
```json
{
  "chats": [
    {
      "id": number,
      "userId": number,
      "unseenMsgs": number,
      "lastMessage": {
        "message": "string",
        "time": "string",
        "senderId": number,
        "msgStatus": {
          "isSent": boolean,
          "isDelivered": boolean,
          "isSeen": boolean
        }
      }
    }
  ]
}
```

#### 1.3. دریافت پیام‌های چت

**Endpoint:** `GET /api/chat/conversations/:conversationId/messages`

**Path Parameters:**
- `conversationId` (number, required): شناسه مکالمه

**Query Parameters:**
- `page?` (number, optional): شماره صفحه
- `limit?` (number, optional): تعداد پیام در هر صفحه

**Response:**
```json
{
  "messages": [
    {
      "message": "string",
      "time": "string",
      "senderId": number,
      "msgStatus": {
        "isSent": boolean,
        "isDelivered": boolean,
        "isSeen": boolean
      }
    }
  ],
  "pagination": {
    "page": number,
    "limit": number,
    "total": number,
    "totalPages": number
  }
}
```

**توضیحات فیلدها:**

| فیلد | نوع | توضیحات |
|------|-----|---------|
| `messages[].message` | string | متن پیام |
| `messages[].time` | string | زمان ارسال (ISO 8601) |
| `messages[].senderId` | number | شناسه فرستنده |
| `messages[].msgStatus.isSent` | boolean | وضعیت ارسال |
| `messages[].msgStatus.isDelivered` | boolean | وضعیت تحویل |
| `messages[].msgStatus.isSeen` | boolean | وضعیت مشاهده |

#### 1.4. ارسال پیام جدید

**Endpoint:** `POST /api/chat/conversations/:conversationId/messages`

**Path Parameters:**
- `conversationId` (number, required): شناسه مکالمه

**Request Body:**
```json
{
  "message": "string"
}
```

**Response:**
```json
{
  "message": {
    "id": number,
    "message": "string",
    "time": "string",
    "senderId": number,
    "msgStatus": {
      "isSent": boolean,
      "isDelivered": boolean,
      "isSeen": boolean
    }
  }
}
```

#### 1.5. به‌روزرسانی وضعیت مشاهده پیام

**Endpoint:** `PUT /api/chat/messages/:messageId/read`

**Path Parameters:**
- `messageId` (number, required): شناسه پیام

**Response:**
```json
{
  "success": boolean
}
```

#### 1.6. دریافت اطلاعات پروفایل کاربر

**Endpoint:** `GET /api/chat/profile`

**Response:**
```json
{
  "profileUser": {
    "id": number,
    "role": "string",
    "about": "string",
    "avatar": "string",
    "fullName": "string",
    "status": "busy" | "away" | "online" | "offline",
    "settings": {
      "isNotificationsOn": boolean,
      "isTwoStepAuthVerificationEnabled": boolean
    }
  }
}
```

---

## 2. AI Chat

**Route:** `/apps/ai-chat`

**دسترسی:** همه کاربران

**نکات مهم:**
- AI Chat باید به تسک‌های Calendar، Kanban، و Todo دسترسی داشته باشد
- AI Chat باید نسبت به برخی پیام‌ها حساس باشد و پردازش ویژه انجام دهد

### API های مورد نیاز

#### 2.1. ارسال پیام به AI

**Endpoint:** `POST /api/ai-chat/messages`

**Request Body:**
```json
{
  "content": "string",
  "images": ["string"],
  "files": [
    {
      "name": "string",
      "data": "string",
      "type": "string",
      "size": number
    }
  ],
  "model": "gpt-4" | "gpt-3.5" | "claude" | "gemini",
  "conversationId": "string"
}
```

**توضیحات فیلدها:**

| فیلد | نوع | توضیحات |
|------|-----|---------|
| `content` | string | متن پیام |
| `images` | string[] | آرایه URL تصاویر (base64 data URLs) |
| `files[].name` | string | نام فایل |
| `files[].data` | string | داده فایل (base64 data URL) |
| `files[].type` | string | نوع MIME فایل |
| `files[].size` | number | حجم فایل (بایت) |
| `model` | string | مدل AI مورد استفاده |
| `conversationId` | string | شناسه مکالمه (اختیاری) |

**Response:**
```json
{
  "message": {
    "id": "string",
    "role": "user" | "assistant",
    "content": "string",
    "images": ["string"],
    "files": [
      {
        "name": "string",
        "data": "string",
        "type": "string",
        "size": number
      }
    ],
    "timestamp": "string",
    "isSensitive": boolean,
    "sensitiveReason": "string"
  },
  "assistantResponse": {
    "id": "string",
    "role": "assistant",
    "content": "string",
    "timestamp": "string",
    "referencedTasks": [
      {
        "taskId": "string",
        "source": "calendar" | "kanban" | "todo",
        "title": "string"
      }
    ]
  }
}
```

**توضیحات فیلدها:**

| فیلد | نوع | توضیحات |
|------|-----|---------|
| `message.isSensitive` | boolean | آیا پیام حساس است |
| `message.sensitiveReason` | string | دلیل حساس بودن پیام |
| `assistantResponse.referencedTasks[].taskId` | string | شناسه تسک |
| `assistantResponse.referencedTasks[].source` | string | منبع تسک (calendar/kanban/todo) |
| `assistantResponse.referencedTasks[].title` | string | عنوان تسک |

#### 2.2. دریافت تاریخچه مکالمه

**Endpoint:** `GET /api/ai-chat/conversations/:conversationId/messages`

**Path Parameters:**
- `conversationId` (string, required): شناسه مکالمه

**Response:**
```json
{
  "messages": [
    {
      "id": "string",
      "role": "user" | "assistant",
      "content": "string",
      "images": ["string"],
      "files": [
        {
          "name": "string",
          "data": "string",
          "type": "string",
          "size": number
        }
      ],
      "timestamp": "string"
    }
  ]
}
```

#### 2.3. دریافت لیست مکالمات

**Endpoint:** `GET /api/ai-chat/conversations`

**Response:**
```json
{
  "conversations": [
    {
      "id": "string",
      "title": "string",
      "lastMessage": "string",
      "timestamp": "string",
      "messageCount": number
    }
  ]
}
```

#### 2.4. دریافت تسک‌های مرتبط (برای AI Chat)

**Endpoint:** `GET /api/ai-chat/tasks`

**Query Parameters:**
- `source?` (string, optional): منبع تسک (calendar, kanban, todo)
- `routine?` (number, optional): نوع روتین (0: NONE, 1: DAILY, 2: WEEKLY, 3: MONTHLY, 4: YEARLY)

**Response:**
```json
{
  "tasks": [
    {
      "id": "string",
      "title": "string",
      "description": "string",
      "deadline": number,
      "routine": 0 | 1 | 2 | 3 | 4,
      "tags": ["string"],
      "source": "calendar" | "kanban" | "todo",
      "status": "string",
      "priority": "high" | "medium" | "low"
    }
  ]
}
```

**نکته:** این API تسک‌هایی که routine = 0 دارند را برمی‌گرداند تا در Calendar، Kanban، و Todo مشترک باشند.

---

## 3. Calendar

**Route:** `/apps/calendar`

**دسترسی:** همه کاربران

**نکات مهم:**
- Calendar باید با Kanban و Todo متصل باشد
- تسک‌هایی که routine = 0 دارند باید در هر سه قابل نمایش باشند

### API های مورد نیاز

#### 3.1. دریافت Event ها

**Endpoint:** `GET /api/events`

**Query Parameters:**
- `start?` (string, optional): تاریخ شروع (ISO 8601)
- `end?` (string, optional): تاریخ پایان (ISO 8601)
- `calendar?` (string, optional): فیلتر بر اساس تقویم (Personal, Business, Family, Holiday, ETC)

**Response:**
```json
{
  "events": [
    {
      "id": "string",
      "title": "string",
      "description": "string",
      "deadline": number,
      "tags": ["string"],
      "author": {
        "name": "string",
        "image": "string"
      },
      "calendar": "Personal" | "Business" | "Family" | "Holiday" | "ETC",
      "start": "string",
      "end": "string",
      "allDay": boolean,
      "extendedProps": {}
    }
  ]
}
```

**توضیحات فیلدها:**

| فیلد | نوع | توضیحات |
|------|-----|---------|
| `events[].id` | string | شناسه یکتا رویداد |
| `events[].title` | string | عنوان رویداد |
| `events[].description` | string | توضیحات رویداد |
| `events[].deadline` | number | مهلت (Unix timestamp) |
| `events[].tags` | string[] | برچسب‌ها |
| `events[].author.name` | string | نام نویسنده |
| `events[].author.image` | string | تصویر نویسنده (URL) |
| `events[].calendar` | string | نوع تقویم |
| `events[].start` | string | زمان شروع (ISO 8601) |
| `events[].end` | string | زمان پایان (ISO 8601) |
| `events[].allDay` | boolean | رویداد تمام روز |

#### 3.2. ایجاد Event جدید

**Endpoint:** `POST /api/events`

**Request Body:**
```json
{
  "title": "string",
  "description": "string",
  "deadline": number,
  "tags": ["string"],
  "calendar": "Personal" | "Business" | "Family" | "Holiday" | "ETC",
  "start": "string",
  "end": "string",
  "allDay": boolean,
  "extendedProps": {}
}
```

**Response:**
```json
{
  "event": {
    "id": "string",
    "title": "string",
    "description": "string",
    "deadline": number,
    "tags": ["string"],
    "author": {
      "name": "string",
      "image": "string"
    },
    "calendar": "string",
    "start": "string",
    "end": "string",
    "allDay": boolean
  }
}
```

#### 3.3. به‌روزرسانی Event

**Endpoint:** `PUT /api/events/:eventId`

**Path Parameters:**
- `eventId` (string, required): شناسه رویداد

**Request Body:**
```json
{
  "title": "string",
  "description": "string",
  "deadline": number,
  "tags": ["string"],
  "calendar": "string",
  "start": "string",
  "end": "string",
  "allDay": boolean
}
```

**Response:**
```json
{
  "event": {
    "id": "string",
    "title": "string",
    "description": "string",
    "deadline": number,
    "tags": ["string"],
    "author": {
      "name": "string",
      "image": "string"
    },
    "calendar": "string",
    "start": "string",
    "end": "string",
    "allDay": boolean
  }
}
```

#### 3.4. حذف Event

**Endpoint:** `DELETE /api/events/:eventId`

**Path Parameters:**
- `eventId` (string, required): شناسه رویداد

**Response:**
```json
{
  "success": boolean
}
```

#### 3.5. دریافت تسک‌های غیرروتین (مشترک با Kanban و Todo)

**Endpoint:** `GET /api/tasks/non-routine`

**Response:**
```json
{
  "tasks": [
    {
      "id": "string",
      "title": "string",
      "description": "string",
      "deadline": number,
      "routine": 0,
      "tags": ["string"],
      "author": {
        "name": "string",
        "image": "string"
      },
      "source": "calendar" | "kanban" | "todo",
      "status": "string",
      "priority": "high" | "medium" | "low"
    }
  ]
}
```

**نکته:** این API فقط تسک‌هایی با `routine = 0` (NONE) را برمی‌گرداند که باید در Calendar، Kanban، و Todo نمایش داده شوند.

---

## 4. Kanban

**Route:** `/apps/kanban`

**دسترسی:** همه کاربران

**نکات مهم:**
- Kanban باید با Calendar و Todo متصل باشد
- تسک‌هایی که routine = 0 دارند باید در هر سه قابل نمایش باشند

### API های مورد نیاز

#### 4.1. دریافت Board Kanban

**Endpoint:** `GET /api/kanban/board`

**Response:**
```json
{
  "columns": [
    {
      "id": number,
      "title": "string",
      "taskIds": [number]
    }
  ],
  "tasks": [
    {
      "id": number,
      "title": "string",
      "badgeText": ["string"],
      "attachments": number,
      "comments": number,
      "assigned": [
        {
          "src": "string",
          "name": "string"
        }
      ],
      "image": "string",
      "dueDate": "string",
      "routine": 0 | 1 | 2 | 3 | 4,
      "description": "string",
      "tags": ["string"],
      "source": "kanban" | "calendar" | "todo"
    }
  ]
}
```

**توضیحات فیلدها:**

| فیلد | نوع | توضیحات |
|------|-----|---------|
| `columns[].id` | number | شناسه یکتا ستون |
| `columns[].title` | string | عنوان ستون |
| `columns[].taskIds` | number[] | شناسه‌های تسک‌های موجود در ستون |
| `tasks[].id` | number | شناسه یکتا تسک |
| `tasks[].title` | string | عنوان تسک |
| `tasks[].badgeText` | string[] | برچسب‌های متن |
| `tasks[].attachments` | number | تعداد پیوست‌ها |
| `tasks[].comments` | number | تعداد کامنت‌ها |
| `tasks[].assigned[].src` | string | تصویر اختصاص یافته (URL) |
| `tasks[].assigned[].name` | string | نام اختصاص یافته |
| `tasks[].image` | string | تصویر تسک (URL) |
| `tasks[].dueDate` | string | تاریخ مهلت (ISO 8601) |
| `tasks[].routine` | number | نوع روتین (0: NONE, 1: DAILY, ...) |
| `tasks[].description` | string | توضیحات تسک |
| `tasks[].tags` | string[] | برچسب‌ها |
| `tasks[].source` | string | منبع تسک |

#### 4.2. ایجاد ستون جدید

**Endpoint:** `POST /api/kanban/columns`

**Request Body:**
```json
{
  "title": "string"
}
```

**Response:**
```json
{
  "column": {
    "id": number,
    "title": "string",
    "taskIds": []
  }
}
```

#### 4.3. به‌روزرسانی ستون

**Endpoint:** `PUT /api/kanban/columns/:columnId`

**Path Parameters:**
- `columnId` (number, required): شناسه ستون

**Request Body:**
```json
{
  "title": "string",
  "taskIds": [number]
}
```

**Response:**
```json
{
  "column": {
    "id": number,
    "title": "string",
    "taskIds": [number]
  }
}
```

#### 4.4. حذف ستون

**Endpoint:** `DELETE /api/kanban/columns/:columnId`

**Path Parameters:**
- `columnId` (number, required): شناسه ستون

**Response:**
```json
{
  "success": boolean
}
```

#### 4.5. ایجاد تسک جدید

**Endpoint:** `POST /api/kanban/tasks`

**Request Body:**
```json
{
  "columnId": number,
  "title": "string",
  "description": "string",
  "badgeText": ["string"],
  "attachments": number,
  "comments": number,
  "assigned": [
    {
      "src": "string",
      "name": "string"
    }
  ],
  "image": "string",
  "dueDate": "string",
  "routine": 0 | 1 | 2 | 3 | 4,
  "tags": ["string"]
}
```

**Response:**
```json
{
  "task": {
    "id": number,
    "title": "string",
    "badgeText": ["string"],
    "attachments": number,
    "comments": number,
    "assigned": [
      {
        "src": "string",
        "name": "string"
      }
    ],
    "image": "string",
    "dueDate": "string",
    "routine": number,
    "description": "string",
    "tags": ["string"],
    "source": "kanban"
  }
}
```

#### 4.6. به‌روزرسانی تسک

**Endpoint:** `PUT /api/kanban/tasks/:taskId`

**Path Parameters:**
- `taskId` (number, required): شناسه تسک

**Request Body:**
```json
{
  "title": "string",
  "description": "string",
  "badgeText": ["string"],
  "attachments": number,
  "comments": number,
  "assigned": [
    {
      "src": "string",
      "name": "string"
    }
  ],
  "image": "string",
  "dueDate": "string",
  "routine": number,
  "tags": ["string"],
  "columnId": number
}
```

**Response:**
```json
{
  "task": {
    "id": number,
    "title": "string",
    "badgeText": ["string"],
    "attachments": number,
    "comments": number,
    "assigned": [
      {
        "src": "string",
        "name": "string"
      }
    ],
    "image": "string",
    "dueDate": "string",
    "routine": number,
    "description": "string",
    "tags": ["string"],
    "source": "string"
  }
}
```

#### 4.7. حذف تسک

**Endpoint:** `DELETE /api/kanban/tasks/:taskId`

**Path Parameters:**
- `taskId` (number, required): شناسه تسک

**Response:**
```json
{
  "success": boolean
}
```

#### 4.8. جابجایی تسک بین ستون‌ها

**Endpoint:** `PUT /api/kanban/tasks/:taskId/move`

**Path Parameters:**
- `taskId` (number, required): شناسه تسک

**Request Body:**
```json
{
  "fromColumnId": number,
  "toColumnId": number,
  "position": number
}
```

**Response:**
```json
{
  "success": boolean,
  "columns": [
    {
      "id": number,
      "title": "string",
      "taskIds": [number]
    }
  ]
}
```

---

## 5. Todo

**Route:** `/todo/all`

**دسترسی:** همه کاربران

**نکات مهم:**
- Todo باید با Calendar و Kanban متصل باشد
- تسک‌هایی که routine = 0 دارند باید در هر سه قابل نمایش باشند

### API های مورد نیاز

#### 5.1. دریافت لیست Todo

**Endpoint:** `GET /api/todos`

**Query Parameters:**
- `status?` (string, optional): وضعیت (pending, in-progress, completed)
- `priority?` (string, optional): اولویت (high, medium, low)
- `label?` (string, optional): برچسب
- `filter?` (string, optional): فیلتر (all, starred, important, completed, trashed)
- `search?` (string, optional): جستجو در عنوان و توضیحات

**Response:**
```json
{
  "todos": [
    {
      "id": number,
      "title": "string",
      "description": "string",
      "status": "pending" | "in-progress" | "completed",
      "priority": "high" | "medium" | "low",
      "startDate": "string",
      "dueDate": "string",
      "createdDate": "string",
      "labels": ["string"],
      "isStarred": boolean,
      "isImportant": boolean,
      "isTrashed": boolean,
      "routine": 0 | 1 | 2 | 3 | 4,
      "source": "todo" | "calendar" | "kanban"
    }
  ],
  "total": number
}
```

**توضیحات فیلدها:**

| فیلد | نوع | توضیحات |
|------|-----|---------|
| `todos[].id` | number | شناسه یکتا todo |
| `todos[].title` | string | عنوان todo |
| `todos[].description` | string | توضیحات todo |
| `todos[].status` | string | وضعیت (pending, in-progress, completed) |
| `todos[].priority` | string | اولویت (high, medium, low) |
| `todos[].startDate` | string | تاریخ شروع (ISO 8601) |
| `todos[].dueDate` | string | تاریخ مهلت (ISO 8601) |
| `todos[].createdDate` | string | تاریخ ایجاد (ISO 8601) |
| `todos[].labels` | string[] | برچسب‌ها |
| `todos[].isStarred` | boolean | نشان شده |
| `todos[].isImportant` | boolean | مهم |
| `todos[].isTrashed` | boolean | حذف شده |
| `todos[].routine` | number | نوع روتین (0: NONE, 1: DAILY, ...) |
| `todos[].source` | string | منبع todo |

#### 5.2. ایجاد Todo جدید

**Endpoint:** `POST /api/todos`

**Request Body:**
```json
{
  "title": "string",
  "description": "string",
  "status": "pending" | "in-progress" | "completed",
  "priority": "high" | "medium" | "low",
  "startDate": "string",
  "dueDate": "string",
  "labels": ["string"],
  "isStarred": boolean,
  "isImportant": boolean,
  "routine": 0 | 1 | 2 | 3 | 4
}
```

**Response:**
```json
{
  "todo": {
    "id": number,
    "title": "string",
    "description": "string",
    "status": "string",
    "priority": "string",
    "startDate": "string",
    "dueDate": "string",
    "createdDate": "string",
    "labels": ["string"],
    "isStarred": boolean,
    "isImportant": boolean,
    "isTrashed": boolean,
    "routine": number,
    "source": "todo"
  }
}
```

#### 5.3. به‌روزرسانی Todo

**Endpoint:** `PUT /api/todos/:todoId`

**Path Parameters:**
- `todoId` (number, required): شناسه todo

**Request Body:**
```json
{
  "title": "string",
  "description": "string",
  "status": "pending" | "in-progress" | "completed",
  "priority": "high" | "medium" | "low",
  "startDate": "string",
  "dueDate": "string",
  "labels": ["string"],
  "isStarred": boolean,
  "isImportant": boolean,
  "isTrashed": boolean,
  "routine": number
}
```

**Response:**
```json
{
  "todo": {
    "id": number,
    "title": "string",
    "description": "string",
    "status": "string",
    "priority": "string",
    "startDate": "string",
    "dueDate": "string",
    "createdDate": "string",
    "labels": ["string"],
    "isStarred": boolean,
    "isImportant": boolean,
    "isTrashed": boolean,
    "routine": number,
    "source": "string"
  }
}
```

#### 5.4. حذف Todo

**Endpoint:** `DELETE /api/todos/:todoId`

**Path Parameters:**
- `todoId` (number, required): شناسه todo

**Response:**
```json
{
  "success": boolean
}
```

#### 5.5. دریافت لیست برچسب‌های موجود

**Endpoint:** `GET /api/todos/labels`

**Response:**
```json
{
  "labels": ["string"]
}
```

---

## 6. User Management

**Route:** `/apps/user/list`, `/apps/user/view`

**دسترسی:** فقط برای ادمین (Admin)

### 6.1. User List

**Route:** `/apps/user/list`

#### API های مورد نیاز

##### 6.1.1. دریافت لیست کاربران

**Endpoint:** `GET /api/admin/users`

**Query Parameters:**
- `role?` (string, optional): فیلتر بر اساس نقش (admin, author, editor, maintainer, subscriber)
- `status?` (string, optional): فیلتر بر اساس وضعیت (active, pending, inactive)
- `search?` (string, optional): جستجو در نام، ایمیل، نام کاربری
- `page?` (number, optional): شماره صفحه
- `limit?` (number, optional): تعداد آیتم در هر صفحه

**Response:**
```json
{
  "users": [
    {
      "id": number,
      "role": "string",
      "email": "string",
      "status": "active" | "pending" | "inactive",
      "avatar": "string",
      "company": "string",
      "country": "string",
      "contact": "string",
      "fullName": "string",
      "username": "string",
      "currentPlan": "string",
      "avatarColor": "primary" | "success" | "error" | "warning" | "info",
      "billing": "string"
    }
  ],
  "pagination": {
    "page": number,
    "limit": number,
    "total": number,
    "totalPages": number
  },
  "stats": {
    "total": number,
    "active": number,
    "pending": number,
    "inactive": number
  }
}
```

**توضیحات فیلدها:**

| فیلد | نوع | توضیحات |
|------|-----|---------|
| `users[].id` | number | شناسه یکتا کاربر |
| `users[].role` | string | نقش کاربر |
| `users[].email` | string | ایمیل کاربر |
| `users[].status` | string | وضعیت کاربر |
| `users[].avatar` | string | آواتار کاربر (URL) |
| `users[].company` | string | نام شرکت |
| `users[].country` | string | کشور |
| `users[].contact` | string | شماره تماس |
| `users[].fullName` | string | نام کامل |
| `users[].username` | string | نام کاربری |
| `users[].currentPlan` | string | پلن فعلی |
| `users[].avatarColor` | ThemeColor | رنگ آواتار (در صورت نبودن تصویر) |
| `users[].billing` | string | روش پرداخت |

##### 6.1.2. ایجاد کاربر جدید

**Endpoint:** `POST /api/admin/users`

**Request Body:**
```json
{
  "role": "string",
  "email": "string",
  "fullName": "string",
  "username": "string",
  "contact": "string",
  "company": "string",
  "country": "string",
  "status": "active" | "pending" | "inactive",
  "currentPlan": "string",
  "avatar": "string"
}
```

**Response:**
```json
{
  "user": {
    "id": number,
    "role": "string",
    "email": "string",
    "status": "string",
    "avatar": "string",
    "company": "string",
    "country": "string",
    "contact": "string",
    "fullName": "string",
    "username": "string",
    "currentPlan": "string",
    "avatarColor": "string",
    "billing": "string"
  }
}
```

##### 6.1.3. به‌روزرسانی کاربر

**Endpoint:** `PUT /api/admin/users/:userId`

**Path Parameters:**
- `userId` (number, required): شناسه کاربر

**Request Body:**
```json
{
  "role": "string",
  "email": "string",
  "fullName": "string",
  "username": "string",
  "contact": "string",
  "company": "string",
  "country": "string",
  "status": "active" | "pending" | "inactive",
  "currentPlan": "string",
  "avatar": "string"
}
```

**Response:**
```json
{
  "user": {
    "id": number,
    "role": "string",
    "email": "string",
    "status": "string",
    "avatar": "string",
    "company": "string",
    "country": "string",
    "contact": "string",
    "fullName": "string",
    "username": "string",
    "currentPlan": "string",
    "avatarColor": "string",
    "billing": "string"
  }
}
```

##### 6.1.4. حذف کاربر

**Endpoint:** `DELETE /api/admin/users/:userId`

**Path Parameters:**
- `userId` (number, required): شناسه کاربر

**Response:**
```json
{
  "success": boolean
}
```

### 6.2. User View

**Route:** `/apps/user/view`

#### API های مورد نیاز

##### 6.2.1. دریافت جزئیات کاربر

**Endpoint:** `GET /api/admin/users/:userId`

**Path Parameters:**
- `userId` (number, required): شناسه کاربر

**Response:**
```json
{
  "user": {
    "id": number,
    "role": "string",
    "email": "string",
    "status": "string",
    "avatar": "string",
    "company": "string",
    "country": "string",
    "contact": "string",
    "fullName": "string",
    "username": "string",
    "currentPlan": "string",
    "avatarColor": "string",
    "billing": "string",
    "joinDate": "string",
    "lastLogin": "string",
    "twoStepVerification": boolean,
    "recentDevices": [
      {
        "id": "string",
        "device": "string",
        "browser": "string",
        "location": "string",
        "lastActive": "string",
        "ip": "string"
      }
    ],
    "activityTimeline": [
      {
        "id": "string",
        "title": "string",
        "description": "string",
        "time": "string",
        "icon": "string",
        "color": "string"
      }
    ],
    "projects": [
      {
        "id": "string",
        "name": "string",
        "startDate": "string",
        "deadline": "string",
        "status": "string",
        "budget": number,
        "spent": number
      }
    ],
    "invoices": [
      {
        "id": "string",
        "total": number,
        "issuedDate": "string",
        "status": "string",
        "balance": number
      }
    ],
    "connections": [
      {
        "id": "string",
        "app": "string",
        "username": "string",
        "avatar": "string",
        "connected": boolean,
        "connectedAt": "string"
      }
    ],
    "notifications": {
      "email": {
        "newComment": boolean,
        "newAnswer": boolean,
        "followMe": boolean,
        "answerOnForm": boolean,
        "productUpdate": boolean,
        "productNewFeature": boolean,
        "productAnnouncement": boolean
      },
      "phone": {
        "newComment": boolean,
        "newAnswer": boolean,
        "followMe": boolean,
        "answerOnForm": boolean
      }
    }
  }
}
```

**توضیحات فیلدها:**

| فیلد | نوع | توضیحات |
|------|-----|---------|
| `user.joinDate` | string | تاریخ عضویت (ISO 8601) |
| `user.lastLogin` | string | آخرین ورود (ISO 8601) |
| `user.twoStepVerification` | boolean | فعال‌سازی احراز هویت دو مرحله‌ای |
| `user.recentDevices[].id` | string | شناسه دستگاه |
| `user.recentDevices[].device` | string | نام دستگاه |
| `user.recentDevices[].browser` | string | مرورگر |
| `user.recentDevices[].location` | string | موقعیت جغرافیایی |
| `user.recentDevices[].lastActive` | string | آخرین فعالیت (ISO 8601) |
| `user.recentDevices[].ip` | string | آدرس IP |
| `user.activityTimeline[].id` | string | شناسه فعالیت |
| `user.activityTimeline[].title` | string | عنوان فعالیت |
| `user.activityTimeline[].description` | string | توضیحات فعالیت |
| `user.activityTimeline[].time` | string | زمان فعالیت (ISO 8601) |
| `user.activityTimeline[].icon` | string | آیکون |
| `user.activityTimeline[].color` | string | رنگ |
| `user.projects[].id` | string | شناسه پروژه |
| `user.projects[].name` | string | نام پروژه |
| `user.projects[].startDate` | string | تاریخ شروع (ISO 8601) |
| `user.projects[].deadline` | string | تاریخ مهلت (ISO 8601) |
| `user.projects[].status` | string | وضعیت پروژه |
| `user.projects[].budget` | number | بودجه |
| `user.projects[].spent` | number | هزینه شده |
| `user.invoices[].id` | string | شناسه فاکتور |
| `user.invoices[].total` | number | مبلغ کل |
| `user.invoices[].issuedDate` | string | تاریخ صدور (ISO 8601) |
| `user.invoices[].status` | string | وضعیت فاکتور |
| `user.invoices[].balance` | number | مانده حساب |
| `user.connections[].id` | string | شناسه اتصال |
| `user.connections[].app` | string | نام اپلیکیشن |
| `user.connections[].username` | string | نام کاربری |
| `user.connections[].avatar` | string | آواتار (URL) |
| `user.connections[].connected` | boolean | وضعیت اتصال |
| `user.connections[].connectedAt` | string | تاریخ اتصال (ISO 8601) |
| `user.notifications.email.*` | boolean | تنظیمات اطلاع‌رسانی ایمیل |
| `user.notifications.phone.*` | boolean | تنظیمات اطلاع‌رسانی تلفن |

##### 6.2.2. به‌روزرسانی تنظیمات امنیتی کاربر

**Endpoint:** `PUT /api/admin/users/:userId/security`

**Path Parameters:**
- `userId` (number, required): شناسه کاربر

**Request Body:**
```json
{
  "twoStepVerification": boolean,
  "currentPassword": "string",
  "newPassword": "string"
}
```

**Response:**
```json
{
  "success": boolean
}
```

##### 6.2.3. به‌روزرسانی تنظیمات اطلاع‌رسانی

**Endpoint:** `PUT /api/admin/users/:userId/notifications`

**Path Parameters:**
- `userId` (number, required): شناسه کاربر

**Request Body:**
```json
{
  "email": {
    "newComment": boolean,
    "newAnswer": boolean,
    "followMe": boolean,
    "answerOnForm": boolean,
    "productUpdate": boolean,
    "productNewFeature": boolean,
    "productAnnouncement": boolean
  },
  "phone": {
    "newComment": boolean,
    "newAnswer": boolean,
    "followMe": boolean,
    "answerOnForm": boolean
  }
}
```

**Response:**
```json
{
  "success": boolean
}
```

---

## 7. Roles & Permissions

**Route:** `/apps/roles`, `/apps/permissions`

**دسترسی:** فقط برای ادمین (Admin)

### 7.1. Roles

**Route:** `/apps/roles`

#### API های مورد نیاز

##### 7.1.1. دریافت لیست نقش‌ها

**Endpoint:** `GET /api/admin/roles`

**Response:**
```json
{
  "roles": [
    {
      "id": "string",
      "name": "string",
      "totalUsers": number,
      "avatars": ["string"],
      "description": "string"
    }
  ],
  "roleStats": {
    "administrator": number,
    "author": number,
    "editor": number,
    "maintainer": number,
    "subscriber": number
  }
}
```

**توضیحات فیلدها:**

| فیلد | نوع | توضیحات |
|------|-----|---------|
| `roles[].id` | string | شناسه یکتا نقش |
| `roles[].name` | string | نام نقش |
| `roles[].totalUsers` | number | تعداد کاربران دارای این نقش |
| `roles[].avatars` | string[] | آواتارهای کاربران (URL) |
| `roles[].description` | string | توضیحات نقش |
| `roleStats.*` | number | آمار کاربران هر نقش |

##### 7.1.2. دریافت کاربران بر اساس نقش

**Endpoint:** `GET /api/admin/roles/:roleName/users`

**Path Parameters:**
- `roleName` (string, required): نام نقش

**Response:**
```json
{
  "users": [
    {
      "id": number,
      "fullName": "string",
      "username": "string",
      "email": "string",
      "avatar": "string",
      "role": "string",
      "status": "string"
    }
  ]
}
```

##### 7.1.3. ایجاد نقش جدید

**Endpoint:** `POST /api/admin/roles`

**Request Body:**
```json
{
  "name": "string",
  "description": "string",
  "permissions": ["string"]
}
```

**Response:**
```json
{
  "role": {
    "id": "string",
    "name": "string",
    "description": "string",
    "totalUsers": number,
    "avatars": [],
    "permissions": ["string"]
  }
}
```

##### 7.1.4. به‌روزرسانی نقش

**Endpoint:** `PUT /api/admin/roles/:roleId`

**Path Parameters:**
- `roleId` (string, required): شناسه نقش

**Request Body:**
```json
{
  "name": "string",
  "description": "string",
  "permissions": ["string"]
}
```

**Response:**
```json
{
  "role": {
    "id": "string",
    "name": "string",
    "description": "string",
    "totalUsers": number,
    "avatars": ["string"],
    "permissions": ["string"]
  }
}
```

##### 7.1.5. حذف نقش

**Endpoint:** `DELETE /api/admin/roles/:roleId`

**Path Parameters:**
- `roleId` (string, required): شناسه نقش

**Response:**
```json
{
  "success": boolean
}
```

### 7.2. Permissions

**Route:** `/apps/permissions`

#### API های مورد نیاز

##### 7.2.1. دریافت لیست Permission ها

**Endpoint:** `GET /api/admin/permissions`

**Query Parameters:**
- `search?` (string, optional): جستجو در نام permission

**Response:**
```json
{
  "permissions": [
    {
      "id": number,
      "name": "string",
      "createdDate": "string",
      "assignedTo": "string" | ["string"]
    }
  ],
  "total": number
}
```

**توضیحات فیلدها:**

| فیلد | نوع | توضیحات |
|------|-----|---------|
| `permissions[].id` | number | شناسه یکتا permission |
| `permissions[].name` | string | نام permission |
| `permissions[].createdDate` | string | تاریخ ایجاد (ISO 8601) |
| `permissions[].assignedTo` | string \| string[] | نقش یا نقش‌های اختصاص یافته |

##### 7.2.2. ایجاد Permission جدید

**Endpoint:** `POST /api/admin/permissions`

**Request Body:**
```json
{
  "name": "string",
  "assignedTo": "string" | ["string"]
}
```

**Response:**
```json
{
  "permission": {
    "id": number,
    "name": "string",
    "createdDate": "string",
    "assignedTo": "string" | ["string"]
  }
}
```

##### 7.2.3. به‌روزرسانی Permission

**Endpoint:** `PUT /api/admin/permissions/:permissionId`

**Path Parameters:**
- `permissionId` (number, required): شناسه permission

**Request Body:**
```json
{
  "name": "string",
  "assignedTo": "string" | ["string"]
}
```

**Response:**
```json
{
  "permission": {
    "id": number,
    "name": "string",
    "createdDate": "string",
    "assignedTo": "string" | ["string"]
  }
}
```

##### 7.2.4. حذف Permission

**Endpoint:** `DELETE /api/admin/permissions/:permissionId`

**Path Parameters:**
- `permissionId` (number, required): شناسه permission

**Response:**
```json
{
  "success": boolean
}
```

---

## 8. Sensor Hub

**Route:** تب مرکز سنسور در Account Settings

**دسترسی:** کاربران احراز هویت شده

### API های مورد نیاز

#### 8.1. دریافت لیست سنسورها

**Endpoint:** `GET /api/sensor-hub/`

**Response:**
```json
{
  "data": [
    {
      "name": "string",
      "uuid_sensor": "string",
      "last_updated": "string"
    }
  ]
}
```

یا در صورت برگرداندن تک سنسور:
```json
{
  "data": {
    "name": "string",
    "uuid_sensor": "string",
    "last_updated": "string"
  }
}
```

#### 8.2. افزودن سنسور جدید

**Endpoint:** `POST /api/sensor-hub/`

**Request Body:**
```json
{
  "name": "string",
  "uuid_sensor": "string",
  "plant_type": "string",
  "plant_name": "string",
  "area_geojson": {},
  "area_m2": number
}
```

**توضیحات فیلدها:**

| فیلد | نوع | الزامی | توضیحات |
|------|-----|--------|---------|
| `name` | string | بله | نام سنسور |
| `uuid_sensor` | string | بله | شناسه یکتای سنسور |
| `plant_type` | string | خیر | نوع محصول (مثل گندم، جو، ذرت) |
| `plant_name` | string | خیر | رقم/نام محصول (وابسته به plant_type) |
| `area_geojson` | object | خیر | محدوده GeoJSON رسم‌شده روی نقشه |
| `area_m2` | number | خیر | مساحت به متر مربع |

#### 8.3. دریافت انواع محصول و ارقام (Plant Types & Varieties)

**Endpoint:** `GET /api/sensor-hub/plant-types`

**توضیح:** این API لیست انواع محصول و ارقام/رقم‌های هر نوع را برمی‌گرداند. فرانت‌اند در فرم افزودن سنسور از این داده برای Autocomplete نوع محصول و رقم استفاده می‌کند.

**Response:**
```json
{
  "plant_types": [
    "گندم",
    "جو",
    "ذرت",
    "برنج",
    "پنبه",
    "چغندر قند",
    "سیب‌زمینی",
    "گوجه‌فرنگی",
    "پیاز",
    "سبزیجات"
  ],
  "plant_names_by_type": {
    "گندم": ["رقم آذر", "رقم شریف", "رقم مروارید", "رقم بهار", "رقم الوند"],
    "جو": ["رقم سرداری", "رقم زاگرس", "رقم کرج", "رقم ریجاب"],
    "ذرت": ["رقم سینگل کراس ۷۰۴", "رقم سینگل کراس ۷۰۷", "رقم ماکزیما"],
    "برنج": ["رقم فجر", "رقم خزر", "رقم طارم"],
    "پنبه": ["رقم ورامین", "رقم ساحل", "رقم سپید"],
    "چغندر قند": ["رقم اکباتان", "رقم شیرین", "رقم پاییزه"],
    "سیب‌زمینی": ["رقم آگریا", "رقم مارفونا", "رقم ساوالان"],
    "گوجه‌فرنگی": ["رقم چری", "رقم روتگرز", "رقم پامیس"],
    "پیاز": ["رقم قرمز آذرشهر", "رقم سفید قم", "رقم زرد"],
    "سبزیجات": ["کاهو", "جعفری", "شوید", "تره", "ریحان"]
  }
}
```

**توضیحات فیلدها:**

| فیلد | نوع | توضیحات |
|------|-----|---------|
| `plant_types` | string[] | آرایه انواع محصول برای انتخاب در Autocomplete |
| `plant_names_by_type` | Record<string, string[]> | نگاشت نوع محصول به لیست ارقام/نام‌های آن |

**نکته:** داده‌های نمونه بالا باید از بک‌اند قابل ویرایش و مدیریت باشند. فرانت‌اند این مقادیر را به‌طور ثابت ندارد و از این API دریافت می‌کند.

---

## خلاصه نکات مهم

1. **Sensor Hub**: فرم افزودن سنسور شامل نوع محصول و رقم می‌شود. لیست `plant_types` و `plant_names_by_type` باید از API دریافت شود، نه به‌صورت ثابت در فرانت.
2. **User Management & Roles & Permissions**: فقط برای ادمین قابل دسترسی هستند
3. **Calendar, Kanban, Todo**: این سه صفحه باید به یکدیگر متصل باشند و تسک‌هایی با `routine = 0` (NONE) در هر سه قابل نمایش باشند
4. **AI Chat**: باید به تسک‌های Calendar، Kanban، و Todo دسترسی داشته باشد و نسبت به برخی پیام‌ها حساس باشد
5. **Authentication**: سیستم Authentication جزو این مستندات نیست

---

## Enum ها و Type های مشترک

### Routine Enum
```typescript
enum Routine {
  NONE = 0,
  DAILY = 1,
  WEEKLY = 2,
  MONTHLY = 3,
  YEARLY = 4
}
```

### ThemeColor Type
```typescript
type ThemeColor = "primary" | "success" | "error" | "warning" | "info"
```

### Status Type (Chat)
```typescript
type StatusType = "busy" | "away" | "online" | "offline"
```

### Todo Status Type
```typescript
type TodoStatusType = "pending" | "in-progress" | "completed"
```

### Todo Priority Type
```typescript
type TodoPriorityType = "high" | "medium" | "low"
```

### Calendar Type
```typescript
type CalendarFiltersType = "Personal" | "Business" | "Family" | "Holiday" | "ETC"
```

### User Role Type
```typescript
type UserRoleType = "admin" | "author" | "editor" | "maintainer" | "subscriber"
```

### User Status Type
```typescript
type UserStatusType = "active" | "pending" | "inactive"
```

---

**تاریخ ایجاد مستندات:** 2024
**نسخه:** 1.0.0

