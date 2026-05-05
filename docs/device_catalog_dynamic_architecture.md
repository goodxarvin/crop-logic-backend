# راهنمای طراحی Device Catalog داینامیک

## هدف

هدف این تغییر این است که اضافه کردن یک دیوایس جدید فقط با ثبت اطلاعات در دیتابیس یا پنل ادمین انجام شود و برای هر دیوایس جدید نیازی به اضافه کردن فایل، ویو، serializer یا service جدید در کد نباشد.

الان ساختار پروژه برای بعضی دیوایس‌ها device-specific است؛ مثلا:

- `device_hub/sensor_7_in_1_urls.py`
- `Sensor7In1SummaryView`
- `get_sensor_7_in_1_summary_data`
- `get_sensor_7_in_1_radar_chart_data`
- `get_sensor_7_in_1_comparison_chart_data`

این ساختار برای یک MVP خوب است، ولی برای scale شدن مناسب نیست. چون برای هر دیوایس جدید باید:

- route جدید بسازید
- view جدید بسازید
- serializer جدید بسازید
- service جدید بسازید
- منطق mapping payload جدید اضافه کنید

این دقیقا چیزی است که باید حذف شود.

---

## مشکل ساختار فعلی

الان backend تا حدی بر اساس `device type` یا `sensor-7-in-1` branch می‌زند، نه بر اساس یک configuration عمومی.

نمونه‌ها:

- `device_hub/views.py`
  - `Sensor7In1SummaryView`
  - `Sensor7In1RadarChartView`
  - `Sensor7In1ComparisonChartView`
- `device_hub/services.py`
  - `get_primary_soil_sensor`
  - `get_sensor_7_in_1_summary_data`
  - `get_sensor_7_in_1_values_list_data`
  - `get_sensor_7_in_1_radar_chart_data`
  - `get_sensor_7_in_1_comparison_chart_data`
- `device_hub/sensor_serializers.py`
  - `Sensor7In1SummarySerializer`
  - `Sensor7In1MetaSerializer`

مشکل این approach:

1. اضافه شدن هر device جدید نیاز به deploy کد دارد.
2. naming پروژه به device خاص وابسته می‌شود.
3. APIها generic نیستند.
4. frontend مجبور می‌شود endpointهای مخصوص هر device را صدا بزند.
5. منطق business به‌جای data-driven بودن، hard-coded شده است.

---

## معماری پیشنهادی

### اصل طراحی

به‌جای این‌که برای هر device endpoint جدا داشته باشیم، باید فقط یک سری endpoint عمومی داشته باشیم که بر اساس:

- `physical_device_uuid`
یا
- `device_catalog_uuid`
یا
- `device_catalog.code`

اطلاعات همان device را برگردانند.

یعنی backend باید:

1. device را پیدا کند
2. configuration آن device را از catalog بخواند
3. payload mapping آن device را بخواند
4. widgetهای قابل نمایش آن را تشخیص دهد
5. خروجی استاندارد بسازد

---

## APIهای پیشنهادی

## راهنمای `device_code`

در این معماری باید بین این سه مفهوم تفاوت روشن باشد:

- `physical_device_uuid`: شناسه خودِ دستگاه ثبت‌شده روی مزرعه
- `device_catalog.uuid`: شناسه رکورد catalog
- `device_code`: مقدار متنی فیلد `DeviceCatalog.code` مثل `soil_sensor_v2` یا `irrigation_valve_v1`

### `device_code` را از کجا می‌گیریم؟

دو راه اصلی برای پیدا کردن `device_code`های یک دستگاه وجود دارد:

#### 1) از جزئیات device

در پاسخ این endpoint:

```http
GET /api/device-hub/devices/{physical_device_uuid}/?device_code=<device_code>
```

فیلدهای زیر برمی‌گردند:

- `data.device_catalog.code`
- `data.device_catalogs[].code`

یعنی frontend می‌تواند codeهای attachشده به device را از همین پاسخ بخواند.

#### 2) از endpoint اختصاصی لیست codeها

```http
GET /api/device-hub/devices/{physical_device_uuid}/device-codes/
```

پاسخ نمونه:

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "physical_device_uuid": "device-uuid",
    "device_codes": ["soil_sensor_v2", "air_sensor_v1"]
  }
}
```

این endpoint برای وقتی مناسب است که frontend فقط می‌خواهد بداند این device به چه `device_code`هایی وصل است.

### `device_code` را کجا باید ارسال کنیم؟

`device_code` همیشه لازم نیست. بسته به endpoint یکی از این حالت‌ها را دارد:

#### الف) در query string

برای endpointهایی که خروجی آن‌ها باید بر اساس یکی از catalogهای attachشده انتخاب شود:

```http
GET /api/device-hub/devices/{physical_device_uuid}/?device_code=soil_sensor_v2
GET /api/device-hub/devices/{physical_device_uuid}/latest/?device_code=soil_sensor_v2
GET /api/device-hub/devices/{physical_device_uuid}/summary/?device_code=soil_sensor_v2
GET /api/device-hub/devices/{physical_device_uuid}/values-list/?device_code=soil_sensor_v2&range=7d
GET /api/device-hub/devices/{physical_device_uuid}/comparison-chart/?device_code=soil_sensor_v2&range=7d
GET /api/device-hub/devices/{physical_device_uuid}/radar-chart/?device_code=soil_sensor_v2&range=7d
GET /api/device-hub/devices/{physical_device_uuid}/logs/?device_code=soil_sensor_v2&page=1&page_size=20
```

#### ب) در body درخواست

برای endpoint command:

```http
POST /api/device-hub/devices/{physical_device_uuid}/commands/
```

نمونه body:

```json
{
  "device_code": "irrigation_valve_v1",
  "command": "open",
  "payload": {
    "duration_seconds": 120
  }
}
```

#### ج) endpointهایی که اصلاً `device_code` نمی‌خواهند

این endpoint فقط با `physical_device_uuid` کار می‌کند:

```http
GET /api/device-hub/devices/{physical_device_uuid}/device-codes/
```

و endpointهای catalog-level هم معمولاً `device_code` لازم ندارند:

```http
GET /api/device-hub/catalog/
```

### چه زمانی `device_code` اجباری است؟

وقتی یک `FarmDevice` ممکن است به چند catalog وصل باشد، backend بدون `device_code` نمی‌تواند بفهمد باید:

- mapping کدام catalog را اعمال کند
- widgetهای کدام catalog را برگرداند
- لاگ را بر اساس کدام catalog فیلتر کند
- command را برای کدام نوع device validate کند

پس در endpointهای data/summary/chart/logs/commands باید `device_code` صریح ارسال شود.

### `device_code` دقیقاً باید چه مقداری باشد؟

باید مقدار فیلد `DeviceCatalog.code` ارسال شود، نه:

- `name`
- `uuid`
- `physical_device_uuid`

مثال درست:

```text
soil_sensor_v2
air_sensor_v1
irrigation_valve_v1
```

مثال اشتباه:

```text
Soil Sensor V2
11111111-1111-1111-1111-111111111111
22222222-2222-2222-2222-222222222222
```

### اگر `device_code` اشتباه باشد چه می‌شود؟

اگر `device_code` به آن device attach نشده باشد، backend باید validation error برگرداند. معمولاً چیزی شبیه این:

```json
{
  "device_code": [
    "Device code is not attached to this farm device."
  ]
}
```

### 1) لیست دیوایس‌ها

```http
GET /api/device-hub/catalog/
```

کاربرد:

- لیست همه device catalogها
- metadata هر catalog
- نوع ارتباط device
- فیلدهای قابل نمایش

---

### 2) جزئیات یک دیوایس ثبت‌شده روی مزرعه

```http
GET /api/device-hub/devices/{physical_device_uuid}/?device_code=soil_sensor_v1
```

نکته:

- در این endpoint، `device_code` باید در query string ارسال شود.
- اگر device فقط یک catalog داشته باشد، از نظر معماری باز هم بهتر است frontend آن را صریح بفرستد.

پاسخ نمونه:

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "uuid": "farm-device-uuid",
    "physical_device_uuid": "device-uuid",
    "name": "Soil Sensor #1",
    "device_catalog": {
      "uuid": "catalog-uuid",
      "code": "soil_sensor_v1",
      "name": "Soil Sensor V1",
      "device_communication_type": "output_only"
    },
    "specifications": {},
    "power_source": {},
    "last_payload_at": "2025-01-01T10:00:00Z"
  }
}
```

---

### 3) آخرین داده‌ی یک device

```http
GET /api/device-hub/devices/{physical_device_uuid}/latest/?device_code=soil_sensor_v1
```

کاربرد:

- آخرین payload خام
- آخرین payload نرمال‌شده
- آخرین readingهای قابل نمایش

---

### 4) summary داینامیک برای یک device

```http
GET /api/device-hub/devices/{physical_device_uuid}/summary/?device_code=soil_sensor_v1
```

کاربرد:

- به‌جای `sensor_7_in_1/summary`
- خروجی بر اساس config همان device

---

### 5) نمودار مقایسه‌ای داینامیک

```http
GET /api/device-hub/devices/{physical_device_uuid}/comparison-chart/?device_code=soil_sensor_v1&range=7d
```

---

### 6) نمودار رادار داینامیک

```http
GET /api/device-hub/devices/{physical_device_uuid}/radar-chart/?device_code=soil_sensor_v1&range=7d
```

---

### 7) values list داینامیک

```http
GET /api/device-hub/devices/{physical_device_uuid}/values-list/?device_code=soil_sensor_v1&range=7d
```

---

### 8) دریافت history خام

```http
GET /api/device-hub/devices/{physical_device_uuid}/logs/?device_code=soil_sensor_v1&page=1&page_size=20
```

این endpoint برای debug و audit خیلی مهم است.

---

## تغییر مهم در مدل‌ها

### 1) `DeviceCatalog`

الان این مدل شروع خوبی دارد، ولی برای dynamic شدن کافی نیست.

مدل فعلی در:

- `device_hub/models.py:6`

فیلدهای پیشنهادی جدید:

```python
display_schema = models.JSONField(default=dict, blank=True)
payload_mapping = models.JSONField(default=dict, blank=True)
supported_widgets = models.JSONField(default=list, blank=True)
commands_schema = models.JSONField(default=list, blank=True)
capabilities = models.JSONField(default=list, blank=True)
```

### توضیح هر فیلد

#### `payload_mapping`

مشخص می‌کند payload خام این device چطور به فیلدهای استاندارد سیستم map شود.

مثال:

```json
{
  "soil_moisture": ["soil_moisture", "soilMoisture", "moisture"],
  "soil_temperature": ["soil_temperature", "soilTemperature", "temperature"],
  "soil_ph": ["soil_ph", "soilPh", "ph"]
}
```

#### `display_schema`

مشخص می‌کند کدام فیلدها در UI نمایش داده شوند و label و unit آن‌ها چیست.

مثال:

```json
{
  "fields": [
    {
      "id": "soil_moisture",
      "label": "رطوبت خاک",
      "unit": "%",
      "ideal_min": 45,
      "ideal_max": 65
    },
    {
      "id": "soil_temperature",
      "label": "دمای خاک",
      "unit": "°C",
      "ideal_min": 18,
      "ideal_max": 28
    }
  ]
}
```

#### `supported_widgets`

مشخص می‌کند برای این device چه widgetهایی فعال باشند.

مثال:

```json
[
  "values_list",
  "comparison_chart",
  "radar_chart",
  "latest_payload",
  "anomaly_card"
]
```

#### `commands_schema`

برای deviceهایی که `input_only` هستند.

مثال:

```json
[
  {
    "command": "turn_on",
    "label": "روشن کردن",
    "payload_schema": {
      "duration_seconds": "integer"
    }
  },
  {
    "command": "turn_off",
    "label": "خاموش کردن",
    "payload_schema": {}
  }
]
```

#### `capabilities`

فهرست capabilityهای device:

```json
["measure", "history", "alert", "command"]
```

---

## برای deviceهای ورودی‌محور

شما گفتی بعضی deviceها فقط باید دستور بگیرند و خروجی نمی‌دهند. این دقیقا باید در مدل و API مشخص باشد.

برای این نوع device:

- `device_communication_type = "input_only"`
- `returned_data_fields = []`
- `supported_widgets = []`
- `commands_schema` باید پر باشد

API پیشنهادی:

```http
POST /api/device-hub/devices/{physical_device_uuid}/commands/
```

payload نمونه:

```json
{
  "device_code": "irrigation_valve_v1",
  "command": "turn_on",
  "payload": {
    "duration_seconds": 120
  }
}
```

پاسخ نمونه:

```json
{
  "code": 200,
  "msg": "command accepted",
  "data": {
    "physical_device_uuid": "device-uuid",
    "command": "turn_on",
    "status": "queued"
  }
}
```

---

## چه جاهایی باید در پروژه تغییر کند

### 1) حذف وابستگی به `sensor_7_in_1`

#### فایل‌هایی که باید refactor شوند

- `device_hub/views.py`
- `device_hub/services.py`
- `device_hub/sensor_serializers.py`
- `device_hub/sensor_7_in_1_urls.py`
- `device_hub/comparison_urls.py`
- `device_hub/urls.py`

#### چه چیزی باید تغییر کند

- viewهای device-specific حذف شوند
- routeهای generic جایگزین شوند
- serviceهای `get_sensor_7_in_1_*` به serviceهای generic تبدیل شوند

---

### 2) ساخت service عمومی برای پیدا کردن device

در `device_hub/services.py` باید این لایه‌ها ایجاد شود:

#### الف) resolver

```python
get_farm_device_by_physical_uuid(physical_device_uuid)
get_device_catalog_for_farm_device(farm_device)
get_latest_device_log(farm_device)
get_device_logs(farm_device, range_value=None)
```

#### ب) normalizer

```python
normalize_device_payload(device_catalog, payload)
extract_device_readings(device_catalog, payload)
```

این بخش باید از `payload_mapping` استفاده کند، نه از `SENSOR_FIELDS` ثابت.

#### ج) presenter / builder

```python
build_device_summary(farm_device)
build_device_values_list(farm_device, range_value)
build_device_comparison_chart(farm_device, range_value)
build_device_radar_chart(farm_device, range_value)
```

---

### 3) ثابت‌های hard-coded باید از کد خارج شوند

الان این موارد hard-coded هستند:

- `SENSOR_FIELDS`
- `COMPARISON_CHART_FIELD_ALIASES`
- `VALUES_LIST_FIELDS`
- `RADAR_CHART_FIELDS`

این‌ها الان در:

- `device_hub/services.py:16`

هستند و باید به config وابسته به `DeviceCatalog` منتقل شوند.

یعنی:

- به‌جای constant سراسری
- از `device_catalog.display_schema`
- و `device_catalog.payload_mapping`

استفاده شود.

---

### 4) serializerهای اختصاصی باید generic شوند

الان در:

- `device_hub/sensor_serializers.py:6`

serializerها مخصوص 7-in-1 هستند.

باید این‌ها جایگزین شوند:

- `DeviceMetaSerializer`
- `DeviceFieldValueSerializer`
- `DeviceValuesListSerializer`
- `DeviceSummarySerializer`
- `DeviceComparisonChartSerializer`
- `DeviceRadarChartSerializer`

یعنی نام serializer نباید به یک device خاص گره خورده باشد.

---

### 5) endpointهای generic بسازید

در `device_hub/urls.py` بهتر است چیزی شبیه این داشته باشید:

```python
urlpatterns = [
    path("catalog/", DeviceCatalogListView.as_view(), name="device-catalog-list"),
    path("devices/<uuid:physical_device_uuid>/device-codes/", DeviceCodeListView.as_view(), name="device-code-list"),
    path("devices/<uuid:physical_device_uuid>/", DeviceDetailView.as_view(), name="device-detail"),
    path("devices/<uuid:physical_device_uuid>/latest/", DeviceLatestPayloadView.as_view(), name="device-latest-payload"),
    path("devices/<uuid:physical_device_uuid>/summary/", DeviceSummaryView.as_view(), name="device-summary"),
    path("devices/<uuid:physical_device_uuid>/values-list/", DeviceValuesListView.as_view(), name="device-values-list"),
    path("devices/<uuid:physical_device_uuid>/comparison-chart/", DeviceComparisonChartView.as_view(), name="device-comparison-chart"),
    path("devices/<uuid:physical_device_uuid>/radar-chart/", DeviceRadarChartView.as_view(), name="device-radar-chart"),
    path("devices/<uuid:physical_device_uuid>/logs/", DeviceLogListView.as_view(), name="device-log-list"),
    path("devices/<uuid:physical_device_uuid>/commands/", DeviceCommandView.as_view(), name="device-command"),
    path("external/", SensorExternalAPIView.as_view(), name="sensor-external-api"),
]
```

---

## روند اضافه کردن device جدید بدون تغییر کد

بعد از این refactor، اضافه کردن device جدید باید این‌طوری باشد:

### مرحله 1

یک رکورد جدید در `DeviceCatalog` ایجاد شود.

### مرحله 2

این اطلاعات برایش ثبت شود:

- `code`
- `name`
- `device_communication_type`
- `payload_mapping`
- `display_schema`
- `supported_widgets`
- `commands_schema`

### مرحله 3

هنگام ثبت `FarmDevice`، آن device به همین catalog وصل شود.

### مرحله 4

از این به بعد frontend فقط با `physical_device_uuid` به endpointهای generic می‌زند.

بدون تغییر کد.

---

## نمونه config برای یک سنسور خروجی‌محور

```json
{
  "code": "soil_sensor_v2",
  "name": "Soil Sensor V2",
  "device_communication_type": "output_only",
  "returned_data_fields": [
    "soil_moisture",
    "soil_temperature",
    "soil_ph"
  ],
  "payload_mapping": {
    "soil_moisture": ["moisture", "soil_moisture"],
    "soil_temperature": ["temperature", "soil_temperature"],
    "soil_ph": ["ph", "soil_ph"]
  },
  "display_schema": {
    "fields": [
      {
        "id": "soil_moisture",
        "label": "رطوبت خاک",
        "unit": "%",
        "ideal_min": 45,
        "ideal_max": 65
      },
      {
        "id": "soil_temperature",
        "label": "دمای خاک",
        "unit": "°C",
        "ideal_min": 18,
        "ideal_max": 28
      },
      {
        "id": "soil_ph",
        "label": "PH خاک",
        "unit": "pH",
        "ideal_min": 6,
        "ideal_max": 7.5
      }
    ]
  },
  "supported_widgets": [
    "values_list",
    "comparison_chart",
    "radar_chart",
    "latest_payload"
  ],
  "commands_schema": []
}
```

---

## نمونه config برای یک device فقط ورودی

مثلا شیر برقی یا پمپ:

```json
{
  "code": "irrigation_valve_v1",
  "name": "Irrigation Valve V1",
  "device_communication_type": "input_only",
  "returned_data_fields": [],
  "payload_mapping": {},
  "display_schema": {
    "fields": []
  },
  "supported_widgets": [],
  "commands_schema": [
    {
      "command": "open",
      "label": "باز کردن شیر",
      "payload_schema": {
        "duration_seconds": "integer"
      }
    },
    {
      "command": "close",
      "label": "بستن شیر",
      "payload_schema": {}
    }
  ]
}
```

---

## پیشنهاد مرحله‌بندی پیاده‌سازی

### فاز 1: Generic read API

اول این‌ها را بسازید:

- `DeviceDetailView`
- `DeviceLatestPayloadView`
- `DeviceSummaryView`
- `DeviceValuesListView`
- `DeviceComparisonChartView`
- `DeviceRadarChartView`

و فعلا داده را با fallback از منطق فعلی بسازید.

### فاز 2: Config-driven normalization

بعد:

- `payload_mapping`
- `display_schema`
- `supported_widgets`

را به `DeviceCatalog` اضافه کنید و منطق hard-coded را حذف کنید.

### فاز 3: Command API

برای `input_only` deviceها:

- `DeviceCommandView`
- command validation
- queue / external broker integration

### فاز 4: Admin / CMS support

برای اینکه بدون کد device جدید اضافه شود، باید از طریق:

- Django Admin
یا
- پنل داخلی

بتوانید `DeviceCatalog` را مدیریت کنید.

---

## حداقل تغییر‌هایی که همین الان باید انجام بدهید

اگر بخواهی با کمترین تغییر از ساختار فعلی به ساختار بهتر برسی، این‌ها مهم‌ترین کارها هستند:

### ضروری

1. حذف endpointهای `sensor_7_in_1`-محور
2. ساخت endpointهای generic با `physical_device_uuid`
3. جدا کردن منطق extraction از device-specific code
4. انتقال field mapping از constant به دیتابیس
5. اضافه کردن schema برای commandها

### مهم ولی فاز بعدی

1. admin برای `DeviceCatalog`
2. validation قوی برای `payload_mapping`
3. caching برای summary/chartها
4. swagger dynamic docs برای command schema

---

## جمع‌بندی

اگر هدفت این است که:

- device جدید بدون تغییر کد اضافه شود
- frontend فقط با `device_uuid` کار کند
- بعضی deviceها فقط command بگیرند
- بعضی deviceها telemetry بدهند

پس باید طراحی از:

- `device-specific code`

به این مدل تغییر کند:

- `catalog-driven architecture`

یعنی:

- `DeviceCatalog` منبع حقیقت باشد
- APIها generic باشند
- parsing و rendering بر اساس config انجام شود
- commandها هم از schema خود device خوانده شوند

---

## فایل‌های کلیدی برای refactor

- `device_hub/models.py:6`
- `device_hub/views.py:19`
- `device_hub/services.py:16`
- `device_hub/sensor_serializers.py:1`
- `device_hub/urls.py:1`
- `device_hub/sensor_7_in_1_urls.py:1`
- `device_hub/comparison_urls.py:1`
- `device_hub/seeds.py:12`

---

## پیشنهاد نهایی

بهترین مسیر این است که:

1. endpointهای generic را اضافه کنی
2. endpointهای قدیمی `sensor_7_in_1` را deprecated کنی
3. config مورد نیاز را به `DeviceCatalog` اضافه کنی
4. frontend را به `physical_device_uuid`-based API منتقل کنی

اگر خواستی، در مرحله بعد من می‌توانم همین طراحی را به تسک اجرایی تبدیل کنم و دقیقا بگویم:

- چه model fieldهایی اضافه شوند
- چه serializerهایی ساخته شوند
- چه endpointهایی پیاده شوند
- و refactor را در چه ترتیب انجام بدهی
