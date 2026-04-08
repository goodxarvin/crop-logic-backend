# Crop Zoning Layer Area API Changes For Frontend

این فایل برای تیم فرانت نوشته شده و فقط تغییرات جدیدی را توضیح می‌دهد که برای endpointهای لایه‌ای ماژول `crop-zoning` اضافه شده‌اند.

## خلاصه تغییر

سه API جدید اضافه شده‌اند که از نظر ساختار response دقیقا شبیه `GET /area/` هستند:

- `GET /api/crop-zoning/water-need/`
- `GET /api/crop-zoning/soil-quality/`
- `GET /api/crop-zoning/cultivation-risk/`

هر سه endpoint:

- به `farm_uuid` نیاز دارند
- از `page` و `page_size` پشتیبانی می‌کنند
- در صورت نبود داده، همان روند ساخت area و zone و dispatch task را مثل `area/` انجام می‌دهند
- همان ساختار `task`, `area`, `zones`, `pagination` را برمی‌گردانند

## هدف این تغییر

قبلا فرانت برای داده‌های لایه‌ای بیشتر به endpointهای `zones/...` متکی بود که خروجی آن‌ها فقط لیست زون‌ها بود.  
الان برای هر لایه یک endpoint جدید دارید که خروجی آن برای صفحه map دقیقا با `area/` هم‌فرمت است و استفاده در UI ساده‌تر می‌شود.

## Base Path

```text
/api/crop-zoning/
```

## Authentication

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

## Endpointهای جدید

### 1) Water Need

```http
GET /api/crop-zoning/water-need/?farm_uuid=<farm_uuid>&page=1&page_size=10
```

### 2) Soil Quality

```http
GET /api/crop-zoning/soil-quality/?farm_uuid=<farm_uuid>&page=1&page_size=10
```

### 3) Cultivation Risk

```http
GET /api/crop-zoning/cultivation-risk/?farm_uuid=<farm_uuid>&page=1&page_size=10
```

## Query Params

- `farm_uuid`: اجباری، UUID مزرعه
- `page`: اختیاری، شماره صفحه زون‌ها، پیش‌فرض `1`
- `page_size`: اختیاری، تعداد زون در هر صفحه، پیش‌فرض `10`

## ساختار کلی response

ساختار کلی هر سه API:

```json
{
  "status": "success",
  "data": {
    "task": {},
    "area": {},
    "zones": [],
    "pagination": {}
  }
}
```

یعنی برای فرانت:

- `task` دقیقا مثل `area/` است
- `area` دقیقا مثل `area/` است
- `pagination` دقیقا مثل `area/` است
- فقط shape آیتم‌های داخل `zones` بر اساس نوع لایه فرق می‌کند

## تفاوت `zones` در هر endpoint

### `GET /water-need/`

هر آیتم در `zones` این فیلدها را دارد:

- `zoneId`
- `zoneUuid`
- `geometry`
- `center`
- `area_sqm`
- `area_hectares`
- `sequence`
- `processing_status`
- `processing_error`
- `waterNeedLayer`

نمونه:

```json
{
  "zoneId": "zone-0",
  "zoneUuid": "d7a9a19b-b3ec-4721-b514-9aae5c9ea940",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[[51.384258, 35.689389], [51.38536404, 35.689389], [51.38536404, 35.69028731], [51.384258, 35.69028731], [51.384258, 35.689389]]]
  },
  "center": {
    "latitude": 35.68983816,
    "longitude": 51.38481102
  },
  "area_sqm": 9999.91,
  "area_hectares": 1,
  "sequence": 0,
  "processing_status": "completed",
  "processing_error": "",
  "waterNeedLayer": {
    "level": "medium",
    "value": "4820-5820 m³/ha",
    "color": "#0ea5e9"
  }
}
```

### `GET /soil-quality/`

هر آیتم در `zones` این فیلدها را دارد:

- `zoneId`
- `zoneUuid`
- `geometry`
- `center`
- `area_sqm`
- `area_hectares`
- `sequence`
- `processing_status`
- `processing_error`
- `soilQualityLayer`

نمونه:

```json
{
  "zoneId": "zone-0",
  "zoneUuid": "d7a9a19b-b3ec-4721-b514-9aae5c9ea940",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[[51.384258, 35.689389], [51.38536404, 35.689389], [51.38536404, 35.69028731], [51.384258, 35.69028731], [51.384258, 35.689389]]]
  },
  "center": {
    "latitude": 35.68983816,
    "longitude": 51.38481102
  },
  "area_sqm": 9999.91,
  "area_hectares": 1,
  "sequence": 0,
  "processing_status": "completed",
  "processing_error": "",
  "soilQualityLayer": {
    "level": "high",
    "score": 89,
    "color": "#22c55e"
  }
}
```

### `GET /cultivation-risk/`

هر آیتم در `zones` این فیلدها را دارد:

- `zoneId`
- `zoneUuid`
- `geometry`
- `center`
- `area_sqm`
- `area_hectares`
- `sequence`
- `processing_status`
- `processing_error`
- `cultivationRiskLayer`

نمونه:

```json
{
  "zoneId": "zone-0",
  "zoneUuid": "d7a9a19b-b3ec-4721-b514-9aae5c9ea940",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[[51.384258, 35.689389], [51.38536404, 35.689389], [51.38536404, 35.69028731], [51.384258, 35.69028731], [51.384258, 35.689389]]]
  },
  "center": {
    "latitude": 35.68983816,
    "longitude": 51.38481102
  },
  "area_sqm": 9999.91,
  "area_hectares": 1,
  "sequence": 0,
  "processing_status": "completed",
  "processing_error": "",
  "cultivationRiskLayer": {
    "level": "low",
    "color": "#22c55e"
  }
}
```

## نکته مهم برای فرانت

این endpointها عمدا شبیه `area/` طراحی شده‌اند تا فرانت بتواند با یک data flow یکسان کار کند:

- polygon اصلی را از `data.area` بگیرد
- task status را از `data.task` بخواند
- pagination را از `data.pagination` بخواند
- فقط renderer مربوط به هر لایه را روی `data.zones` اعمال کند

## پیشنهاد استفاده در UI

### اگر صفحه overview اصلی دارید

- همچنان `GET /area/` بهترین گزینه برای صفحه overview کامل است، چون علاوه بر layerها فیلدهای crop و recommendation را هم داخل هر zone دارد.

### اگر صفحه یا tab مخصوص هر layer دارید

- برای تب نیاز آبی: `GET /water-need/`
- برای تب کیفیت خاک: `GET /soil-quality/`
- برای تب ریسک کشت: `GET /cultivation-risk/`

این کار باعث می‌شود فرانت فقط داده موردنیاز همان layer را بگیرد.

## وضعیت backward compatibility

- endpoint قدیمی `GET /area/` بدون تغییر باقی مانده است
- endpointهای جدید breaking change ایجاد نمی‌کنند
- فقط سه مسیر جدید به API اضافه شده است

## خطاها

رفتار خطاها مثل `area/` است.

### نبودن `farm_uuid`

```json
{
  "status": "error",
  "message": "farm_uuid is required."
}
```

### پیدا نشدن مزرعه

```json
{
  "status": "error",
  "message": "Farm not found."
}
```

### نامعتبر بودن `page` یا `page_size`

```json
{
  "status": "error",
  "message": "page must be a positive integer."
}
```

## جمع‌بندی

تغییر جدید برای فرانت این است که الان به جز `area/`، سه API جدید هم دارید که:

- از نظر query params شبیه `area/` هستند
- از نظر response wrapper شبیه `area/` هستند
- فقط payload داخلی `zones` را بر اساس نوع layer تخصصی می‌کنند

در نتیجه اگر UI شما برای `area/` آماده است، اتصال این سه endpoint جدید باید با کمترین تغییر انجام شود.
