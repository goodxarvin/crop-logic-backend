# راهنمای فرانت برای API های Location Data

این فایل برای تیم فرانت نوشته شده تا بتواند API های `Location Data` را سریع و دقیق مصرف کند.

مسیرهای اصلی:

- `GET /api/location-data/`
- `POST /api/location-data/`
- `POST /api/location-data/ndvi-health/`
- `GET /api/location-data/remote-sensing/`
- `POST /api/location-data/remote-sensing/`
- `GET /api/location-data/remote-sensing/cluster-blocks/{cluster_uuid}/live/`
- `GET /api/location-data/remote-sensing/cluster-recommendations/`
- `GET /api/location-data/remote-sensing/results/{result_id}/k-options/`
- `POST /api/location-data/remote-sensing/results/{result_id}/k-options/activate/`
- `GET /api/location-data/remote-sensing/runs/{run_id}/status/`

## احراز هویت

همه این endpointها با JWT کار می‌کنند.

نمونه header:

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

## ساختار عمومی response

تقریبا همه endpointها این فرم را دارند:

```json
{
  "code": 200,
  "msg": "success",
  "data": {}
}
```

قاعده پیشنهادی در فرانت:

1. اول `HTTP status` را چک کنید.
2. بعد `code` را از body چک کنید.
3. در موفقیت، فقط `data` را به state یا UI بدهید.
4. در خطا، `msg` را به عنوان پیام اصلی نمایش دهید.
5. اگر `data` شامل خطای فیلدها بود، آن را برای فرم map کنید.

نمونه خطای validation:

```json
{
  "code": 400,
  "msg": "داده نامعتبر.",
  "data": {
    "farm_uuid": ["This field is required."]
  }
}
```

نمونه خطای not found:

```json
{
  "code": 404,
  "msg": "location پیدا نشد.",
  "data": null
}
```

---

## 1) دریافت location ذخیره شده

### `GET /api/location-data/`

کاربرد:

- خواندن location ذخیره شده
- دریافت farm boundary
- دریافت block layout
- دریافت subdivisionها و snapshotهای ماهواره ای ذخیره شده

### query params

- `lat` اختیاری
- `lon` اختیاری
- `farm_uuid` اختیاری

### نمونه درخواست

```http
GET /api/location-data/?farm_uuid=<farm_uuid>
```

### نمونه response

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "source": "database",
    "id": 12,
    "lon": "51.389000",
    "lat": "35.689200",
    "input_block_count": 2,
    "farm_boundary": {},
    "block_layout": {},
    "block_subdivisions": [],
    "satellite_snapshots": []
  }
}
```

### استفاده در فرانت

- `farm_boundary` را برای رسم polygon کل مزرعه استفاده کنید.
- `block_layout` را برای رندر blockها استفاده کنید.
- `block_subdivisions` برای نمایش grid/subdivision مفید است.
- `satellite_snapshots` برای summaryهای تاریخی یا cache قابل استفاده است.

---

## 2) ثبت یا به روزرسانی location

### `POST /api/location-data/`

کاربرد:

- ساخت location جدید
- update location قبلی
- ثبت farm boundary
- ثبت block layout

### نمونه body

```json
{
  "farm_uuid": "11111111-1111-1111-1111-111111111111",
  "lat": 35.6892,
  "lon": 51.389,
  "farm_boundary": {
    "type": "Polygon",
    "coordinates": []
  },
  "block_layout": {
    "blocks": []
  }
}
```

### نکات فرانت

- اگر کاربر هنوز boundary را کامل نکرده، این endpoint را صدا نزنید.
- در صورت دریافت `source = created` می‌توانید UI را به عنوان location جدید mark کنید.
- در صورت دریافت `source = database` یعنی رکورد از قبل وجود داشته یا update شده است.

---

## 3) دریافت NDVI health

### `POST /api/location-data/ndvi-health/`

کاربرد:

- گرفتن کارت سلامت پوشش گیاهی مزرعه
- نمایش شاخص NDVI در UI

### body

```json
{
  "farm_uuid": "11111111-1111-1111-1111-111111111111"
}
```

### response مهم

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "ndviIndex": 0.63,
    "mean_ndvi": 0.63,
    "ndvi_map": {},
    "vegetation_health_class": "healthy",
    "observation_date": "2026-05-12",
    "satellite_source": "sentinel-2",
    "healthData": [
      {
        "title": "میانگین NDVI",
        "value": 0.63,
        "color": "green",
        "icon": "leaf"
      }
    ]
  }
}
```

### استفاده در فرانت

- `ndviIndex` را به عنوان KPI اصلی نمایش دهید.
- `vegetation_health_class` را برای badge یا رنگ وضعیت استفاده کنید.
- `healthData` را برای کارت های summary استفاده کنید.
- `ndvi_map` اگر لایه نقشه داشت، به map layer وصل شود.

---

## 4) خواندن cache سنجش از دور

### `GET /api/location-data/remote-sensing/`

کاربرد:

- فقط داده cache شده یا ذخیره شده را می‌خواند
- پردازش جدید شروع نمی‌کند

### query params

- `farm_uuid` اجباری
- `page` اختیاری
- `page_size` اختیاری
- `start_date` اختیاری
- `end_date` اختیاری

### نمونه درخواست

```http
GET /api/location-data/remote-sensing/?farm_uuid=<farm_uuid>&page=1&page_size=50
```

### فیلدهای مهم response

- `status`
- `source`
- `location`
- `summary`
- `cells`
- `run`
- `subdivision_result`
- `pagination`
- `metadata`

### رفتار پیشنهادی در فرانت بر اساس `status`

- `success`: داده آماده است و باید render شود.
- `processing`: هنوز نتیجه نهایی آماده نیست؛ loading یا polling state نشان دهید.
- `not_found`: هنوز تحلیل برای این مزرعه ساخته نشده؛ می‌توانید `POST /remote-sensing/` را بزنید.

### استفاده در فرانت

- `cells` برای نقشه سلولی و heatmap مناسب است.
- `summary` برای کارت آماری بالای صفحه مناسب است.
- `subdivision_result.cluster_blocks` برای نمایش cluster polygonها استفاده شود.
- `assignments` برای رنگ آمیزی سلول ها بر اساس label کلاستر مفید است.

---

## 5) شروع تحلیل سنجش از دور

### `POST /api/location-data/remote-sensing/`

کاربرد:

- شروع async processing
- ساخت run و `task_id`
- شروع جریان polling برای UI

### body

```json
{
  "farm_uuid": "11111111-1111-1111-1111-111111111111"
}
```

### response

```json
{
  "code": 202,
  "msg": "تحلیل سنجش‌ازدور در صف قرار گرفت.",
  "data": {
    "status": "processing",
    "source": "processing",
    "location": {},
    "block_code": "",
    "chunk_size_sqm": 900,
    "temporal_extent": {
      "start_date": "2026-04-12",
      "end_date": "2026-05-12"
    },
    "summary": {
      "cell_count": 0,
      "ndvi_mean": null,
      "ndwi_mean": null,
      "soil_vv_db_mean": null
    },
    "cells": [],
    "run": {},
    "task_id": "11111111-1111-1111-1111-111111111111"
  }
}
```

### قرارداد مهم برای فرانت

- همیشه `task_id` را ذخیره کنید.
- اگر `run.id` موجود بود، برای status endpoint از آن استفاده کنید.
- بعد از این endpoint بلافاصله polling را شروع کنید.

### flow پیشنهادی

```text
POST /remote-sensing/
-> دریافت task_id / run
-> هر چند ثانیه GET /runs/{run_id}/status/
-> وقتی status = completed شد، همان payload را مصرف کن
```

---

## 6) دریافت live metrics برای یک cluster

### `GET /api/location-data/remote-sensing/cluster-blocks/{cluster_uuid}/live/`

کاربرد:

- گرفتن metricهای یک cluster
- استفاده برای panel جزئیات یا modal زنده

### نمونه درخواست

```http
GET /api/location-data/remote-sensing/cluster-blocks/<cluster_uuid>/live/
```

### فیلدهای مهم

- `source`
- `cluster_block`
- `summary`
- `metrics`
- `metadata`

### نکات فرانت

- اگر `source = database` بود، label بزنید که داده cache است.
- اگر `source = openeo` بود، می‌توانید label زنده یا live نمایش دهید.
- `metrics` برای KPIهای سریع مناسب است.
- `cluster_block.geometry` را برای هایلایت روی نقشه استفاده کنید.

---

## 7) پیشنهاد گیاه برای clusterها

### `GET /api/location-data/remote-sensing/cluster-recommendations/`

کاربرد:

- دریافت پیشنهاد محصول برای هر cluster
- نمایش candidate plantها و suggested plant

### query params

- `farm_uuid` اجباری

نمونه:

```http
GET /api/location-data/remote-sensing/cluster-recommendations/?farm_uuid=<farm_uuid>
```

### فیلدهای مهم response

- `farm_uuid`
- `location_id`
- `registered_plants`
- `clusters`
- `evaluated_plant_count`
- `cluster_count`
- `source_metadata`

### نکات مهم برای فرانت

- هر آیتم `clusters` دقیقا مربوط به یک cluster از خروجی KMeans است.
- `candidate_plants` لیست کامل رتبه‌بندی است و `suggested_plant` بهترین آیتم همان لیست است.
- `resolved_metrics` همان متریک نهایی است که برای simulation استفاده شده و بهتر است مبنای نمایش KPI باشد.
- `cluster_block` برای رسم روی نقشه و نمایش geometry، centroid و cellها استفاده می‌شود.
- `source_metadata.has_sensor_metrics` مشخص می‌کند آیا باید در UI بخش سنسورها را نمایش دهید یا نه.

### استفاده در فرانت

برای هر cluster این بخش ها مهم هستند:

- `sub_block_code`
- `cluster_label`
- `temporal_extent`
- `cluster_block`
- `satellite_metrics`
- `sensor_metrics`
- `resolved_metrics`
- `candidate_plants`
- `suggested_plant`

### UI پیشنهادی

- کارت cluster با عنوان `sub_block_code` یا `cluster_label`
- بازه زمانی از `temporal_extent.start_date` تا `temporal_extent.end_date`
- KPIهای `resolved_metrics`
- جدول candidateها با score
- highlight کردن `suggested_plant`
- اگر `candidate_plants` خالی بود، state خالی و بدون recommendation نشان دهید

---

## 8) لیست K optionها

### `GET /api/location-data/remote-sensing/results/{result_id}/k-options/`

کاربرد:

- گرفتن همه Kهای ذخیره شده برای یک subdivision result

### response مهم

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "result_id": 5,
    "active_requested_k": 3,
    "recommended_requested_k": 4,
    "options": []
  }
}
```

### استفاده در فرانت

- `active_requested_k` را به عنوان گزینه فعال UI نشان دهید.
- `recommended_requested_k` را با badge پیشنهادی نمایش دهید.
- `options` را برای dropdown یا segmented control استفاده کنید.

---

## 9) فعال سازی یک K

### `POST /api/location-data/remote-sensing/results/{result_id}/k-options/activate/`

### body

```json
{
  "requested_k": 4
}
```

### استفاده در فرانت

- وقتی کاربر K جدید را انتخاب می‌کند این endpoint را صدا بزنید.
- بعد از موفقیت، `subdivision_result` برگشتی را جایگزین state قبلی کنید.
- لازم نیست دوباره `GET /remote-sensing/` را صدا بزنید اگر payload کامل برگشت.

---

## 10) polling وضعیت run

### `GET /api/location-data/remote-sensing/runs/{run_id}/status/`

کاربرد:

- فهمیدن این که pipeline در چه مرحله‌ای است
- دریافت نتیجه نهایی به محض completion

### statusهای مهم

- `pending`
- `running`
- `retrying`
- `completed`
- `failed`

### رفتار پیشنهادی در فرانت

- `pending`: queue state
- `running`: progress state
- `retrying`: پیام retry موقت
- `completed`: داده نهایی را render کن
- `failed`: CTA برای retry بده

### نکته مهم

اگر `status = completed` شد، همان response نهایی را مصرف کنید و polling را stop کنید.

---

## فیلدهای مهم برای map

### farm level

- `farm_boundary`
- `block_layout.blocks`
- `block_subdivisions`

### remote sensing level

- `cells[].geometry`
- `subdivision_result.cluster_blocks[].geometry`
- `subdivision_result.assignments[]`
- `cluster_block.geometry`

### پیشنهاد برای لایه های نقشه

1. لایه مرز مزرعه
2. لایه blockها
3. لایه cellها یا heatmap
4. لایه cluster blockها
5. لایه selected cluster highlight

---

## خطاهایی که فرانت باید handle کند

### 400

- ورودی ناقص یا نامعتبر
- باید خطای فیلدی یا toast نشان داده شود

### 404

- مزرعه یا location یا result پیدا نشده
- برای UI بهتر است empty state نمایش داده شود

### 502

- خطا از backend upstream مثل openEO یا AI
- بهتر است retry action داشته باشید

---

## flow پیشنهادی کامل برای صفحه تحلیل

### سناریو اول: فقط نمایش داده موجود

```text
GET /api/location-data/remote-sensing/?farm_uuid=<farm_uuid>
-> اگر status=success : render
-> اگر status=processing : برو به polling
-> اگر status=not_found : دکمه شروع تحلیل نمایش بده
```

### سناریو دوم: کاربر تحلیل را شروع می‌کند

```text
POST /api/location-data/remote-sensing/
-> 202
-> run/task_id را ذخیره کن
-> GET /api/location-data/remote-sensing/runs/{run_id}/status/
-> وقتی completed شد نتیجه را render کن
```

### سناریو سوم: کاربر K را تغییر می‌دهد

```text
GET /results/{result_id}/k-options/
-> انتخاب K
-> POST /results/{result_id}/k-options/activate/
-> subdivision_result جدید را render کن
```

---

## پیشنهاد state management در فرانت

حداقل stateهایی که نیاز دارید:

```ts
{
  location: null,
  remoteSensing: null,
  runStatus: null,
  clusterRecommendations: [],
  selectedClusterUuid: null,
  kOptions: [],
  loading: false,
  polling: false,
  error: null
}
```

---

## نکات نهایی برای تیم فرانت

- برای endpointهای async همیشه polling را در نظر بگیرید.
- `code` را از body نادیده نگیرید.
- روی `status` در remote sensing و run status منطق UI بنویسید.
- داده های هندسی را مستقیم برای map layerها مصرف کنید.
- `cluster_uuid`, `result_id`, `run_id` را بعد از اولین response در state نگه دارید.

---

## فایل مکمل

اگر به جزئیات کامل همه responseها نیاز دارید، این فایل را هم ببینید:

- `docs/location_data_api_responses_fa.md`
