# مستندات کامل API های `access_control`

این فایل بر اساس پیاده‌سازی واقعی در `access_control/urls.py`, `access_control/views.py`, `access_control/permissions.py`, `access_control/middleware.py`, `access_control/services.py` و `config/feature.json` تهیه شده است.

نکته مهم: ماژول دسترسی فقط دو endpoint مستقیم ندارد؛ بخشی از منطق دسترسی به‌صورت سراسری روی کل پروژه اعمال می‌شود. بنابراین در این مستند هم APIهای مستقیم و هم رفتار سراسری access control توضیح داده شده‌اند.

## مشخصات کلی

- Base path:

```text
/api/access-control/
```

- احراز هویت:

تمام endpointهای این ماژول نیاز به کاربر لاگین‌شده دارند.

```http
Authorization: Bearer <token>
```

- فرمت کلی پاسخ موفق:

```json
{
  "code": 200,
  "msg": "success",
  "data": {}
}
```

- فرمت خطاهای مربوط به دسترسی:

```json
{
  "code": 403,
  "msg": "error",
  "data": {
    "detail": "Access denied."
  }
}
```

یا برای route-level denial:

```json
{
  "code": 403,
  "msg": "Access to route feature `farm_management` is denied."
}
```

---

## لیست endpointهای مستقیم

| Method | URL | توضیح |
|---|---|---|
| POST | `/api/access-control/farms/{farm_uuid}/authorize/` | بررسی دسترسی کاربر برای یک یا چند feature روی یک مزرعه |
| GET | `/api/access-control/panel-routing/` | تعیین پنل مناسب کاربر لاگین‌شده |

---

## 1) بررسی دسترسی featureها برای یک مزرعه

### Request

```http
POST /api/access-control/farms/{farm_uuid}/authorize/
Authorization: Bearer <token>
Content-Type: application/json
```

### Path Param

- `farm_uuid`: شناسه مزرعه‌ای که دسترسی باید روی آن بررسی شود.

### Body

```json
{
  "features": [
    "greenhouse-dashboard",
    "sensor-7-in-1"
  ],
  "action": "view"
}
```

### فیلدهای ورودی

- `features`
  - نوع: `array[string]`
  - اجباری: بله
  - خالی بودن لیست مجاز نیست.
- `action`
  - نوع: `string`
  - اجباری: خیر
  - مقدار پیش‌فرض: `view`

### رفتار

- ابتدا بررسی می‌شود که کاربر به آن مزرعه دسترسی دارد یا نه.
- سپس درخواست به سرویس authorization ارسال می‌شود.
- داده‌های کاربر، مزرعه، پلن اشتراک، محصولات و سنسورها در payload authorization لحاظ می‌شوند.
- نتیجه تصمیم‌گیری به‌شکل خام در فیلد `decision` برگردانده می‌شود.

### Response 200

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "farm_uuid": "11111111-1111-1111-1111-111111111111",
    "user": {
      "id": 7,
      "username": "admin",
      "email": "admin@example.com",
      "phone_number": "0912345678"
    },
    "features": [
      "greenhouse-dashboard",
      "sensor-7-in-1"
    ],
    "action": "view",
    "decision": {
      "decisions": {
        "greenhouse-dashboard": true,
        "sensor-7-in-1": false
      }
    }
  }
}
```

### Response 404

```json
{
  "code": 404,
  "msg": "Farm not found."
}
```

### Response 503

```json
{
  "code": 503,
  "msg": "..."
}
```

این حالت زمانی رخ می‌دهد که سرویس authorization در دسترس نباشد.

---

## 2) تعیین پنل کاربر

### Request

```http
GET /api/access-control/panel-routing/
Authorization: Bearer <token>
```

### رفتار

- نقش کاربر از روی `role` یا `is_staff` / `is_superuser` تعیین می‌شود.
- اگر کاربر admin باشد، `panel=admin` برگردانده می‌شود.
- در غیر این صورت `panel=user` برمی‌گردد.

### Response 200

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "panel": "admin",
    "role": "admin",
    "permissions": []
  }
}
```

---

## منطق سراسری دسترسی در کل پروژه

ماژول `access_control` فقط این دو endpoint را ارائه نمی‌دهد؛ بلکه به‌صورت global روی بیشتر APIهای پروژه اعمال می‌شود.

## 3) Middleware سراسری route-level access

فایل:

```text
access_control/middleware.py
```

### رفتار

- برای درخواست‌های authenticated اجرا می‌شود.
- app جاری را از روی view تشخیص می‌دهد.
- feature متناظر با app را از `config/feature.json` پیدا می‌کند.
- در صورت وجود `farm_uuid`، مزرعه را نیز resolve می‌کند.
- سپس با `authorize_feature(...)` بررسی می‌کند که کاربر مجاز است یا نه.

### خطاهای middleware

- اگر route ادمینی باشد و کاربر admin نباشد:

```json
{
  "code": 403,
  "msg": "Admin access is required for this route."
}
```

- اگر feature آن route برای کاربر مجاز نباشد:

```json
{
  "code": 403,
  "msg": "Access to route feature `feature_code` is denied."
}
```

- اگر سرویس access control در دسترس نباشد:

```json
{
  "code": 503,
  "msg": "..."
}
```

---

## 4) Permission سراسری DRF

فایل:

```text
access_control/permissions.py
```

و در `config/settings.py` به‌صورت global فعال شده است:

```python
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
        "access_control.permissions.FeatureAccessPermission",
    ],
}
```

### رفتار

- اگر view دارای `required_feature_code` باشد، access دقیق همان feature بررسی می‌شود.
- اگر view دارای `admin_only = True` باشد، فقط admin اجازه دارد.
- اگر `farm_uuid` برای view لازم باشد ولی ارسال نشود، permission رد می‌شود.

### نمونه viewهای feature-based

- `dashboard/views.py`
  - `required_feature_code = "greenhouse-dashboard"`
- `device_hub/views.py`
  - `required_feature_code = "sensor-7-in-1"`

یعنی این endpointها علاوه بر login، به access rule هم وابسته‌اند.

---

## 5) نگاشت app به feature

فایل:

```text
config/feature.json
```

### mapping فعلی

| App | Feature Code |
|---|---|
| `auth` | `auth_access` |
| `account` | `account_management` |
| `farm_hub` | `farm_management` |
| `access_control` | `access_control` |
| `sensor_catalog` | `sensor_catalog` |
| `dashboard` | `farm_dashboard` |
| `crop_zoning` | `crop_zoning` |
| `plant_simulator` | `plant_simulator` |
| `pest_detection` | `pest_detection` |
| `sensor_7_in_1` | `sensor-7-in-1` |
| `irrigation` | `irrigation` |
| `fertilization` | `fertilization` |
| `farm_ai_assistant` | `farm_ai_assistant` |
| `notifications` | `notifications` |
| `external_api_adapter` | `external_api_adapter` |
| `sensor_external_api` | `sensor_external_api` |

### admin route prefixes

در همین فایل مسیرهای ادمینی هم تعریف می‌شوند:

```json
{
  "admin_route_prefixes": [
    "/api/admin/"
  ]
}
```

هر route که با یکی از این prefixها شروع شود، فقط برای admin قابل دسترسی است.

---

## 6) نقش کاربر چگونه تعیین می‌شود؟

در `access_control/services.py` نقش کاربر به این شکل استخراج می‌شود:

- اگر user دارای فیلد `role` باشد، همان استفاده می‌شود.
- اگر `is_staff=True` یا `is_superuser=True` باشد، نقش `admin` در نظر گرفته می‌شود.
- در غیر این صورت نقش `farmer` در نظر گرفته می‌شود.

---

## 7) actionهای استاندارد authorization

در access control، متد HTTP به actionهای زیر map می‌شود:

| HTTP Method | Action |
|---|---|
| `GET` | `view` |
| `HEAD` | `view` |
| `OPTIONS` | `view` |
| `POST` | `create` |
| `PUT` | `edit` |
| `PATCH` | `edit` |
| `DELETE` | `delete` |

این mapping در `access_control/services.py` تعریف شده است.

---

## 8) ورودی‌ای که برای سرویس authorization ساخته می‌شود

برای بررسی دسترسی، payload تقریبی زیر ساخته می‌شود:

```json
{
  "input": {
    "user": {
      "id": 7,
      "username": "admin",
      "email": "admin@example.com",
      "phone_number": "0912345678",
      "is_staff": true,
      "is_superuser": true,
      "role": "admin"
    },
    "resource": {
      "farm_id": "11111111-1111-1111-1111-111111111111",
      "subscription_plan_codes": [
        "gold"
      ],
      "farm_types": [
        "گلخانه ای"
      ],
      "crop_types": [
        "گوجه‌فرنگی"
      ],
      "cultivation_types": [],
      "sensor_codes": [
        "sensor_7_soil_moisture_sensor_v1_2"
      ],
      "power_sensor": [
        "solar"
      ],
      "customization": []
    },
    "features": [
      "greenhouse-dashboard"
    ],
    "action": "view",
    "route": "/api/dashboard/cards/"
  }
}
```

---

## 9) نکات پیاده‌سازی مهم

- endpointهای `access_control` فقط برای query مستقیم دسترسی هستند؛ enforcement اصلی در middleware و permission انجام می‌شود.
- اگر endpointی `required_feature_code` نداشته باشد، فقط login روی آن enforce می‌شود مگر middleware route آن را map کرده باشد.
- اگر access service down باشد، بسته به محل خطا، پاسخ `503` از middleware یا view برگردانده می‌شود.
- اگر permission در DRF رد شود، پاسخ استاندارد خطا از `config/exception_handler.py` برگردانده می‌شود.

---

## جمع‌بندی

اگر بخواهی "APIهای دسترسی" را در این پروژه بشناسی، باید این سه لایه را با هم ببینی:

1. endpointهای مستقیم `access_control`
2. middleware سراسری route-based access
3. permissionهای DRF برای viewهای دارای `required_feature_code`

به همین دلیل، کنترل دسترسی در این پروژه فقط یک endpoint ساده نیست، بلکه بخشی از زیرساخت کل API است.
