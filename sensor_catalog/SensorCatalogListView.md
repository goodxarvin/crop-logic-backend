# مستند API کاتالوگ سنسورها

این فایل API ثبت‌شده در `sensor_catalog/urls.py` را به‌صورت کامل توضیح می‌دهد.

## فایل route

فایل route این app:

`sensor_catalog/urls.py`

محتوای آن:

```python
from django.urls import path

from .views import SensorCatalogListView

urlpatterns = [
    path("", SensorCatalogListView.as_view(), name="sensor-catalog-list"),
]
```

## آدرس نهایی endpoint

این route در `config/urls.py` این‌طور mount شده است:

```python
path("api/sensor-catalog/", include("sensor_catalog.urls"))
```

پس آدرس نهایی API این است:

`GET /api/sensor-catalog/`

## هدف API

این endpoint برای گرفتن لیست کاتالوگ سنسورها استفاده می‌شود.

منظور از کاتالوگ سنسور، تعریف مرجع هر نوع سنسور است؛ مثلا:

- کد سنسور
- نام سنسور
- توضیحات
- فیلدهای خروجی سنسور
- نمونه payload
- منبع تغذیه‌های پشتیبانی‌شده

این API بیشتر برای frontend یا تنظیمات سیستم مفید است تا بداند چه نوع سنسورهایی در سیستم تعریف شده‌اند و هر سنسور چه ساختاری دارد.

## View مربوطه

این endpoint در فایل `sensor_catalog/views.py` پیاده‌سازی شده است:

```python
class SensorCatalogListView(APIView):
    permission_classes = [IsAuthenticated]
```

این یعنی:

- فقط متد `GET` پشتیبانی می‌شود
- کاربر باید authenticated باشد

## احراز هویت و دسترسی

این View از:

```python
permission_classes = [IsAuthenticated]
```

استفاده می‌کند.

در این پروژه به‌صورت پیش‌فرض authentication از طریق JWT انجام می‌شود، چون در `config/settings.py` مقدار زیر تعریف شده:

```python
"DEFAULT_AUTHENTICATION_CLASSES": [
    "rest_framework_simplejwt.authentication.JWTAuthentication",
]
```

پس اگر کاربر توکن معتبر نداشته باشد، این API پاسخ `401 Unauthorized` برمی‌گرداند.

## رفتار endpoint

در متد `get` این View:

```python
def get(self, request):
    sensors = SensorCatalog.objects.order_by("code")
    data = SensorCatalogSerializer(sensors, many=True).data
    return Response({"code": 200, "msg": "success", "data": data}, status=status.HTTP_200_OK)
```

این منطق اجرا می‌شود:

1. همه رکوردهای `SensorCatalog` از دیتابیس خوانده می‌شوند
2. خروجی بر اساس `code` مرتب می‌شود
3. داده‌ها با serializer به JSON تبدیل می‌شوند
4. پاسخ استاندارد با `code` و `msg` و `data` برگردانده می‌شود

## مدل دیتابیس

مدل این API در `sensor_catalog/models.py` قرار دارد:

```python
class SensorCatalog(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    code = models.CharField(max_length=255, unique=True, db_index=True)
    name = models.CharField(max_length=255, unique=True, db_index=True)
    description = models.TextField(blank=True, default="")
    customizable_fields = models.JSONField(default=list, blank=True)
    supported_power_sources = models.JSONField(default=list, blank=True)
    returned_data_fields = models.JSONField(default=list, blank=True)
    sample_payload = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### معنی فیلدها

- `uuid`: شناسه یکتا برای هر کاتالوگ
- `code`: کد یکتا و فنی سنسور
- `name`: نام قابل نمایش سنسور
- `description`: توضیح سنسور
- `customizable_fields`: فیلدهایی که موقع ساخت/پیکربندی سنسور ممکن است قابل تنظیم باشند
- `supported_power_sources`: نوع منبع تغذیه‌های پشتیبانی‌شده
- `returned_data_fields`: فیلدهایی که این سنسور در payload خود برمی‌گرداند
- `sample_payload`: یک نمونه payload برای درک ساختار داده
- `is_active`: فعال یا غیرفعال بودن این کاتالوگ
- `created_at` و `updated_at`: زمان ایجاد و آخرین بروزرسانی

## Serializer خروجی

serializer این endpoint در `sensor_catalog/serializers.py` تعریف شده است:

```python
class SensorCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorCatalog
        fields = [
            "uuid",
            "code",
            "name",
            "description",
            "customizable_fields",
            "supported_power_sources",
            "returned_data_fields",
            "sample_payload",
            "is_active",
        ]
        read_only_fields = fields
```

### نکته مهم

این serializer فقط این فیلدها را در خروجی برمی‌گرداند:

- `uuid`
- `code`
- `name`
- `description`
- `customizable_fields`
- `supported_power_sources`
- `returned_data_fields`
- `sample_payload`
- `is_active`

پس فیلدهای `created_at` و `updated_at` در پاسخ این API نیستند.

## ورودی API

این endpoint ورودی body یا query param خاصی ندارد.

فقط کافی است کاربر authenticated باشد.

### نمونه درخواست

```http
GET /api/sensor-catalog/
Authorization: Bearer <access_token>
```

## خروجی موفق

نمونه پاسخ موفق:

```json
{
  "code": 200,
  "msg": "success",
  "data": [
    {
      "uuid": "11111111-1111-1111-1111-111111111111",
      "code": "sensor_7_soil_moisture_sensor_v1_2",
      "name": "Sensor 7 - Soil Moisture Sensor v1.2",
      "description": "Measures only soil moisture using electrical resistance between two metal probes.",
      "customizable_fields": [],
      "supported_power_sources": ["solar", "direct_power"],
      "returned_data_fields": ["soil_moisture", "analog_output", "digital_output"],
      "sample_payload": {
        "soil_moisture": 42,
        "analog_output": 610,
        "digital_output": 1
      },
      "is_active": true
    },
    {
      "uuid": "22222222-2222-2222-2222-222222222222",
      "code": "legacy_sensor",
      "name": "Legacy Sensor",
      "description": "",
      "customizable_fields": [],
      "supported_power_sources": ["direct_power"],
      "returned_data_fields": ["status"],
      "sample_payload": {
        "status": "offline"
      },
      "is_active": false
    }
  ]
}
```

## ترتیب خروجی

خروجی با این دستور مرتب می‌شود:

```python
SensorCatalog.objects.order_by("code")
```

یعنی لیست همیشه بر اساس `code` به صورت صعودی برگردانده می‌شود.

## سناریوهای کاربردی

این API معمولا برای این موارد استفاده می‌شود:

- ساخت dropdown برای انتخاب نوع سنسور
- نمایش ساختار داده قابل انتظار از یک سنسور
- فهمیدن اینکه هر سنسور چه فیلدهایی برمی‌گرداند
- ساخت فرم‌های داینامیک برای پیکربندی سنسور
- نمایش `sample_payload` در Swagger یا UI مدیریتی

## وضعیت‌های خطا

### 401 Unauthorized

اگر کاربر login نباشد یا توکن معتبر نداشته باشد.

### 200 با لیست خالی

اگر هیچ رکوردی در جدول `sensor_catalogs` وجود نداشته باشد، پاسخ موفق است اما `data` خالی خواهد بود:

```json
{
  "code": 200,
  "msg": "success",
  "data": []
}
```

## تست موجود

برای این endpoint تست در فایل `sensor_catalog/tests.py` وجود دارد.

تست اصلی بررسی می‌کند که:

- کاربر authenticated بتواند endpoint را صدا بزند
- پاسخ `200` باشد
- همه سنسورهای موجود برگردانده شوند

نمونه assertion:

```python
self.assertEqual(response.status_code, 200)
self.assertEqual(response.data["code"], 200)
self.assertEqual(len(response.data["data"]), 2)
```

## خلاصه

API موجود در `sensor_catalog/urls.py` فقط یک endpoint دارد:

- `GET /api/sensor-catalog/`

این endpoint:

- نیاز به احراز هویت دارد
- همه کاتالوگ‌های سنسور را از دیتابیس می‌خواند
- آن‌ها را بر اساس `code` مرتب می‌کند
- اطلاعات ساختاری سنسورها را برای frontend یا پنل مدیریتی برمی‌گرداند

## فایل‌های مرتبط

- `sensor_catalog/urls.py`
- `sensor_catalog/views.py`
- `sensor_catalog/serializers.py`
- `sensor_catalog/models.py`
- `sensor_catalog/tests.py`
- `config/urls.py`
