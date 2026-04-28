# مستند API دریافت داده سنسور خارجی

این فایل رفتار endpoint زیر را توضیح می‌دهد:

`POST /api/sensor-external-api/`

این API برای دریافت payload از یک سنسور فیزیکی، ثبت آن داخل دیتابیس، ساخت نوتیفیکیشن برای مزرعه، و سپس ارسال همان داده به سرویس AI/Farm Data استفاده می‌شود.

## هدف API

این endpoint وقتی صدا زده می‌شود که یک سنسور خارجی داده جدیدی تولید کرده باشد. بک‌اند در این مسیر چند کار پشت سر هم انجام می‌دهد:

1. اعتبارسنجی API key
2. اعتبارسنجی `uuid` و `payload`
3. پیدا کردن سنسور بر اساس `physical_device_uuid`
4. ذخیره لاگ درخواست در جدول `sensor_external_request_logs`
5. ساخت notification برای مزرعه
6. ارسال داده به سرویس AI در endpoint مربوط به farm data

## مسیر و View

این endpoint در فایل `sensor_external_api/urls.py` ثبت شده است:

```python
path("", SensorExternalAPIView.as_view(), name="sensor-external-api")
```

پیاده‌سازی view در فایل `sensor_external_api/views.py` قرار دارد:

```python
class SensorExternalAPIView(APIView):
    authentication_classes = [SensorExternalAPIKeyAuthentication]
    permission_classes = [AllowAny]
```

## احراز هویت

این API از هدر `X-API-Key` استفاده می‌کند.

کلاس احراز هویت:

`sensor_external_api/authentication.py`

رفتار آن:

- اگر `X-API-Key` یا `Authorization` ارسال نشود، پاسخ `401` می‌دهد.
- اگر مقدار کلید اشتباه باشد، پاسخ `401` می‌دهد.
- مقدار مورد انتظار از `SENSOR_EXTERNAL_API_KEY` خوانده می‌شود.

## ورودی درخواست

serializer ورودی در فایل `sensor_external_api/serializers.py` تعریف شده است:

```python
class SensorExternalRequestSerializer(serializers.Serializer):
    uuid = serializers.UUIDField()
    payload = serializers.JSONField(required=False, default=dict)
```

### بدنه نمونه درخواست

```json
{
  "uuid": "22222222-2222-2222-2222-222222222222",
  "payload": {
    "moisture_percent": 32.5,
    "temperature_c": 21.3,
    "ph": 6.7,
    "ec_ds_m": 1.1,
    "nitrogen_mg_kg": 42,
    "phosphorus_mg_kg": 18,
    "potassium_mg_kg": 210
  }
}
```

نکته:

- `uuid` در این API همان `physical_device_uuid` سنسور است.
- `payload` به همان شکلی که از سنسور می‌آید ذخیره و forward می‌شود.

## روند اجرای API

### 1) اعتبارسنجی request

در متد `post` ابتدا داده ورودی validate می‌شود:

```python
serializer = SensorExternalRequestSerializer(data=request.data)
serializer.is_valid(raise_exception=True)
```

اگر `uuid` معتبر نباشد یا ساختار body خراب باشد، DRF خطای `400` برمی‌گرداند.

### 2) ثبت لاگ و ساخت نوتیفیکیشن

سپس این سرویس صدا زده می‌شود:

```python
notification = create_sensor_external_notification(
    physical_device_uuid=serializer.validated_data["uuid"],
    payload=serializer.validated_data.get("payload"),
)
```

این تابع در فایل `sensor_external_api/services.py` قرار دارد.

کارهایی که انجام می‌دهد:

- سنسور را از جدول `FarmSensor` با `physical_device_uuid` پیدا می‌کند.
- اگر سنسور پیدا نشود، `ValueError("Physical device not found.")` می‌دهد.
- یک رکورد در جدول `sensor_external_request_logs` می‌سازد.
- یک notification برای مزرعه می‌سازد.

### رکوردی که در دیتابیس ذخیره می‌شود

مدل ذخیره‌سازی:

`sensor_external_api/models.py`

```python
class SensorExternalRequestLog(models.Model):
    farm_uuid = models.UUIDField(db_index=True)
    sensor_catalog_uuid = models.UUIDField(null=True, blank=True, db_index=True)
    physical_device_uuid = models.UUIDField(db_index=True)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

یعنی payload خام سنسور برای گزارش‌گیری و استفاده‌های بعدی نگه داشته می‌شود.

### 3) ارسال داده به سرویس AI / Farm Data

بعد از ثبت لاگ، این سرویس صدا زده می‌شود:

```python
forward_sensor_payload_to_farm_data(
    physical_device_uuid=serializer.validated_data["uuid"],
    payload=serializer.validated_data.get("payload"),
)
```

این قسمت مهم‌ترین call خارجی endpoint است.

## این API چه آدرسی از AI را صدا می‌زند؟

سرویس خارجی از طریق `external_api_adapter.request` صدا زده می‌شود:

```python
response = external_api_request(
    "ai",
    _get_farm_data_path(),
    method="POST",
    payload=request_payload,
    headers={...},
)
```

### service name

مقدار service برابر است با:

`"ai"`

یعنی این درخواست به سرویسی می‌رود که در تنظیمات به عنوان AI service تعریف شده است.

### base URL سرویس AI

در `config/settings.py`:

```python
"ai": {
    "base_url": os.getenv("AI_SERVICE_BASE_URL", "http://ai-web:8000"),
    "api_key": os.getenv("AI_SERVICE_API_KEY", ""),
    "host_header": os.getenv("AI_SERVICE_HOST_HEADER", "localhost"),
}
```

پس base URL به‌صورت پیش‌فرض این است:

`http://ai-web:8000`

### path مقصد

path از این تنظیم خوانده می‌شود:

```python
FARM_DATA_API_PATH = os.getenv("FARM_DATA_API_PATH", "/api/farm-data/")
```

پس path پیش‌فرض این است:

`/api/farm-data/`

### آدرس نهایی که صدا زده می‌شود

در حالت پیش‌فرض، آدرس نهایی به این صورت است:

`POST http://ai-web:8000/api/farm-data/`

اگر متغیرهای environment تغییر کرده باشند، این آدرس هم تغییر می‌کند.

## چرا این آدرس صدا زده می‌شود؟

هدف از این call این است که داده سنسور خام فقط در بک‌اند ذخیره نشود، بلکه برای پردازش downstream هم به سرویس AI/Farm Data فرستاده شود.

این سرویس AI احتمالا برای کارهای زیر استفاده می‌شود:

- تحلیل داده سنسورها در سطح مزرعه
- ساخت داده تجمیعی farm data
- تغذیه dashboardها و مدل‌های AI
- محاسبه شاخص‌ها یا توصیه‌های بعدی

خود این endpoint در این پروژه فقط داده را forward می‌کند و پردازش AI داخل همین اپ انجام نمی‌شود.

## چه payloadی به AI ارسال می‌شود؟

قبل از ارسال، بک‌اند این ساختار را می‌سازد:

```python
request_payload = {
    "farm_uuid": str(sensor.farm.farm_uuid),
    "farm_boundary": farm_boundary,
    "sensor_payload": {
        sensor.name or str(sensor.physical_device_uuid): payload,
    },
}
```

یعنی payload ارسال‌شده به AI دقیقا body اولیه کاربر نیست، بلکه این wrapper را دارد:

```json
{
  "farm_uuid": "11111111-1111-1111-1111-111111111111",
  "farm_boundary": {
    "type": "Polygon",
    "coordinates": [[[51.39, 35.7], [51.41, 35.7], [51.41, 35.72], [51.39, 35.72], [51.39, 35.7]]]
  },
  "sensor_payload": {
    "Soil Sensor 7-in-1": {
      "moisture_percent": 32.5,
      "temperature_c": 21.3,
      "ph": 6.7,
      "ec_ds_m": 1.1,
      "nitrogen_mg_kg": 42,
      "phosphorus_mg_kg": 18,
      "potassium_mg_kg": 210
    }
  }
}
```

## farm_boundary از کجا می‌آید؟

سرویس `_get_farm_boundary` این منطق را دارد:

- اگر `farm.current_crop_area` وجود داشته باشد، از آن استفاده می‌کند.
- اگر وجود نداشته باشد، آخرین crop area مزرعه را برمی‌دارد.
- اگر هیچ boundary وجود نداشته باشد، خطا می‌دهد.
- اگر geometry از نوع `Polygon` نباشد، خطا می‌دهد.

پس سرویس AI فقط وقتی صدا زده می‌شود که مرز مزرعه معتبر وجود داشته باشد.

## هدرهایی که به AI ارسال می‌شوند

در زمان forward کردن، این هدرها ارسال می‌شوند:

```python
headers={
    "Accept": "application/json",
    "Content-Type": "application/json",
    "X-API-Key": api_key,
    "Authorization": f"Api-Key {api_key}",
}
```

`api_key` از این setting می‌آید:

`FARM_DATA_API_KEY`

اگر این مقدار ست نشده باشد، پاسخ `503` برمی‌گردد.

## پاسخ موفق

اگر همه چیز درست باشد:

- لاگ ذخیره می‌شود
- notification ساخته می‌شود
- داده به AI forward می‌شود
- پاسخ `201` برمی‌گردد

نمونه ساختار پاسخ:

```json
{
  "code": 201,
  "msg": "success",
  "data": {
    "...": "serialized notification object"
  }
}
```

نکته:

data خروجی این endpoint نتیجه AI نیست. خروجی، notification ساخته‌شده در سیستم خود بک‌اند است.

## خطاهای ممکن

### 401 Unauthorized

اگر API key ارسال نشود یا اشتباه باشد.

### 404 Not Found

اگر `physical_device_uuid` در جدول `FarmSensor` پیدا نشود.

پاسخ:

```json
{
  "code": 404,
  "msg": "Physical device not found."
}
```

### 503 Service Unavailable

در چند حالت:

- migration جدول‌ها انجام نشده باشد
- `FARM_DATA_API_KEY` تنظیم نشده باشد
- مرز مزرعه موجود نباشد
- geometry مزرعه `Polygon` نباشد
- سرویس AI در دسترس نباشد
- سرویس AI پاسخ خطای 4xx/5xx بدهد

نمونه خطا:

```json
{
  "code": 503,
  "msg": "Farm data API request failed: connection error"
}
```

## خلاصه رفتاری endpoint

`POST /api/sensor-external-api/` این کارها را انجام می‌دهد:

1. داده سنسور را از بیرون می‌گیرد.
2. سنسور را با `physical_device_uuid` پیدا می‌کند.
3. payload را در جدول لاگ ذخیره می‌کند.
4. برای مزرعه notification می‌سازد.
5. داده را به سرویس AI در آدرس پیش‌فرض `POST http://ai-web:8000/api/farm-data/` می‌فرستد.
6. در نهایت نتیجه موفقیت را با notification برمی‌گرداند.
