# مستند API لاگ درخواست های سنسور خارجی

این فایل نحوه کار endpoint زیر را توضیح می دهد:

`GET /sensor_external_api/logs/`

مسیر مربوطه در فایل `sensor_external_api/urls.py` به این صورت ثبت شده است:

```python
path("logs/", SensorExternalRequestLogListAPIView.as_view(), name="sensor-external-api-log-list")
```

## هدف API

این API برای مشاهده لیست لاگ درخواست هایی استفاده می شود که از سنسورهای خارجی برای یک مزرعه مشخص ثبت شده اند.

هر لاگ شامل اطلاعات زیر است:
- شناسه لاگ
- `farm_uuid`
- `sensor_catalog_uuid`
- `physical_device_uuid`
- `payload` دریافتی از سنسور
- زمان ثبت لاگ
- اطلاعات سنسور مزرعه (`farm_sensor`)
- اطلاعات کاتالوگ سنسور (`sensor_catalog`)

## کلاس View

این endpoint در کلاس `SensorExternalRequestLogListAPIView` داخل فایل `sensor_external_api/views.py` پیاده سازی شده است.

ویژگی های مهم این View:
- فقط متد `GET` را پشتیبانی می کند.
- نیاز به احراز هویت دارد.
- از صفحه بندی استفاده می کند.
- لاگ ها را بر اساس `farm_uuid` فیلتر می کند.

## احراز هویت و دسترسی

در این View مقدار زیر تعریف شده است:

```python
permission_classes = [IsAuthenticated]
```

یعنی کاربر باید authenticated باشد تا بتواند این API را صدا بزند.

نکته مهم:
در تست ها، اگر درخواست بدون اعتبارنامه ارسال شود، پاسخ `401 Unauthorized` برمی گردد.

## پارامترهای ورودی

این API پارامترهای query string زیر را دریافت می کند:

- `farm_uuid` اجباری
- `page` اختیاری، پیش فرض `1`
- `page_size` اختیاری، پیش فرض `20` و حداکثر `100`

اعتبارسنجی پارامترها توسط `SensorExternalRequestLogQuerySerializer` در فایل `sensor_external_api/serializers.py` انجام می شود:

```python
class SensorExternalRequestLogQuerySerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField()
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)
```

### نمونه درخواست

```http
GET /api/sensor-external-api/logs/?farm_uuid=11111111-1111-1111-1111-111111111111&page=1&page_size=20
```

## روند اجرای API

### 1) اعتبارسنجی query params
ابتدا `request.query_params` توسط serializer اعتبارسنجی می شود:

```python
serializer = SensorExternalRequestLogQuerySerializer(data=request.query_params)
serializer.is_valid(raise_exception=True)
```

اگر `farm_uuid` معتبر نباشد یا `page_size` خارج از بازه باشد، پاسخ خطای validation از DRF برمی گردد.

### 2) گرفتن لاگ های مربوط به مزرعه
سپس سرویس `get_sensor_external_request_logs_for_farm` فراخوانی می شود:

```python
queryset = get_sensor_external_request_logs_for_farm(
    farm_uuid=serializer.validated_data["farm_uuid"],
)
```

این سرویس در فایل `sensor_external_api/services.py` تعریف شده و لاگ ها را از جدول `sensor_external_request_logs` می خواند:

```python
SensorExternalRequestLog.objects.filter(farm_uuid=farm_uuid).order_by("-created_at", "-id")
```

پس ترتیب خروجی به این صورت است:
- جدیدترین لاگ ها اول نمایش داده می شوند.
- اگر `created_at` برابر باشد، لاگ با `id` بزرگ تر زودتر می آید.

### 3) مدیریت خطای migration
اگر جدول های لازم هنوز migrate نشده باشند، سرویس خطا را به `ValueError` تبدیل می کند و View این پاسخ را برمی گرداند:

```json
{
  "code": 503,
  "msg": "Required tables are not ready. Run migrations."
}
```

با status code برابر با `503 Service Unavailable`.

### 4) صفحه بندی نتایج
این View از paginator زیر استفاده می کند:

```python
class SensorExternalRequestLogPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
```

و در View نیز `page_size` از داده معتبرشده serializer روی paginator اعمال می شود:

```python
paginator = self.pagination_class()
paginator.page_size = serializer.validated_data["page_size"]
page = paginator.paginate_queryset(queryset, request, view=self)
```

### 5) ساخت map از سنسورهای مزرعه
برای اینکه هر لاگ همراه با اطلاعات سنسور مزرعه و کاتالوگ سنسور برگردد، این سرویس صدا زده می شود:

```python
farm_sensor_map = get_farm_sensor_map_for_logs(logs=page)
```

این سرویس:
- لاگ های همان page را می گیرد.
- `FarmSensor` های متناظر را از دیتابیس پیدا می کند.
- یک map با کلید زیر می سازد:

```python
(farm_uuid, sensor_catalog_uuid, physical_device_uuid)
```

به کمک این map، serializer می تواند برای هر لاگ اطلاعات تکمیلی را پر کند.

## ساختار serializer خروجی

خروجی هر آیتم با `SensorExternalRequestLogSerializer` ساخته می شود.

فیلدهای اصلی:

```python
fields = [
    "id",
    "farm_uuid",
    "sensor_catalog_uuid",
    "physical_device_uuid",
    "farm_sensor",
    "sensor_catalog",
    "payload",
    "created_at",
]
```

### فیلد `farm_sensor`
این فیلد از نوع `SerializerMethodField` است.
اگر سنسور متناظر پیدا شود، اطلاعاتی مثل موارد زیر را برمی گرداند:
- `uuid`
- `sensor_catalog_uuid`
- `physical_device_uuid`
- `name`
- `sensor_type`
- `is_active`
- `specifications`
- `power_source`
- `created_at`
- `updated_at`

اگر سنسور پیدا نشود، مقدار آن `null` خواهد بود.

### فیلد `sensor_catalog`
این فیلد هم از نوع `SerializerMethodField` است.
اگر `farm_sensor` و `sensor_catalog` موجود باشند، اطلاعات کاتالوگ سنسور برمی گردد، مثل:
- `uuid`
- `code`
- `name`
- `description`
- `customizable_fields`
- `supported_power_sources`
- `returned_data_fields`
- `sample_payload`
- `is_active`
- `created_at`
- `updated_at`

اگر داده متناظر وجود نداشته باشد، مقدار آن `null` خواهد بود.

## مدل لاگ

لاگ ها در مدل `SensorExternalRequestLog` ذخیره می شوند:

```python
class SensorExternalRequestLog(models.Model):
    farm_uuid = models.UUIDField(db_index=True)
    sensor_catalog_uuid = models.UUIDField(null=True, blank=True, db_index=True)
    physical_device_uuid = models.UUIDField(db_index=True)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

ویژگی مهم مدل:
- جدول دیتابیس: `sensor_external_request_logs`
- ترتیب پیش فرض: `ordering = ["-created_at", "-id"]`

## نمونه پاسخ موفق

```json
{
  "code": 200,
  "msg": "success",
  "count": 2,
  "next": "http://example.com/api/sensor-external-api/logs/?farm_uuid=11111111-1111-1111-1111-111111111111&page=2&page_size=1",
  "previous": null,
  "data": [
    {
      "id": 12,
      "farm_uuid": "11111111-1111-1111-1111-111111111111",
      "sensor_catalog_uuid": "22222222-2222-2222-2222-222222222222",
      "physical_device_uuid": "55555555-5555-5555-5555-555555555555",
      "farm_sensor": {
        "uuid": "99999999-9999-9999-9999-999999999999",
        "sensor_catalog_uuid": "22222222-2222-2222-2222-222222222222",
        "physical_device_uuid": "55555555-5555-5555-5555-555555555555",
        "name": "External device 2",
        "sensor_type": "soil_sensor",
        "is_active": true,
        "specifications": {
          "model": "FH-2"
        },
        "power_source": {
          "type": "solar"
        },
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T10:00:00Z"
      },
      "sensor_catalog": {
        "uuid": "22222222-2222-2222-2222-222222222222",
        "code": "ext-sensor-log-2",
        "name": "External Sensor Log 2",
        "description": "Sensor catalog for second log",
        "customizable_fields": [],
        "supported_power_sources": [],
        "returned_data_fields": ["humidity"],
        "sample_payload": {},
        "is_active": true,
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T10:00:00Z"
      },
      "payload": {
        "temp": 18
      },
      "created_at": "2024-01-02T10:00:00Z"
    }
  ]
}
```

## خطاهای احتمالی

### 401 Unauthorized
اگر کاربر احراز هویت نشده باشد:

```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 400 Bad Request
اگر پارامترها نامعتبر باشند، مثلا `farm_uuid` فرمت درست نداشته باشد یا `page_size` بیشتر از `100` باشد، خطای validation برگردانده می شود.

### 503 Service Unavailable
اگر migration های مربوط به جدول ها اجرا نشده باشند:

```json
{
  "code": 503,
  "msg": "Required tables are not ready. Run migrations."
}
```

## نکات مهم پیاده سازی

- این API فقط لاگ های مربوط به یک `farm_uuid` را برمی گرداند.
- پاسخ به صورت paginated است.
- داده های `farm_sensor` و `sensor_catalog` به صورت enrich شده به هر لاگ اضافه می شوند.
- اگر برای یک لاگ، سنسور متناظر در `FarmSensor` پیدا نشود، فیلدهای `farm_sensor` و `sensor_catalog` ممکن است `null` باشند.
- ترتیب نمایش لاگ ها نزولی و از جدیدترین به قدیمی ترین است.

## فایل های مرتبط

- `sensor_external_api/urls.py`
- `sensor_external_api/views.py`
- `sensor_external_api/serializers.py`
- `sensor_external_api/services.py`
- `sensor_external_api/models.py`
- `sensor_external_api/tests.py`

## جمع بندی

API مربوط به `logs/` برای گزارش گیری و مشاهده تاریخچه درخواست های ورودی از سنسورهای خارجی یک مزرعه استفاده می شود. این endpoint با دریافت `farm_uuid`، لاگ های مرتبط را از دیتابیس می خواند، آن ها را صفحه بندی می کند، اطلاعات سنسور و کاتالوگ را به خروجی اضافه می کند و در نهایت پاسخ استاندارد برمی گرداند.
