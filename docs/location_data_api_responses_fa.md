# مستند کامل response های Location Data

این فایل، response همه endpointهای اصلی `Location Data` را به زبان ساده و دقیق توضیح می‌دهد.

مسیرهای این مستند:

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

## 1) ساختار عمومی همه response ها

تقریبا همه endpointها این envelope را دارند:

```json
{
  "code": 200,
  "msg": "success",
  "data": {}
}
```

توضیح فیلدها:

- `code`: کد منطقی response در body
- `msg`: پیام کوتاه
- `data`: payload اصلی

در خطاها معمولا یکی از این دو حالت برمی‌گردد:

```json
{
  "code": 400,
  "msg": "داده نامعتبر.",
  "data": {
    "field_name": ["error message"]
  }
}
```

یا:

```json
{
  "code": 404,
  "msg": "location پیدا نشد.",
  "data": null
}
```

## 2) `GET /api/location-data/`

کاربرد:

- خواندن ساختار ذخیره‌شده مزرعه
- خواندن بلوک‌ها
- خواندن subdivisionها
- خواندن snapshotهای ماهواره‌ای ذخیره/تجمیع‌شده

### response موفق `200`

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

### توضیح فیلدهای `data`

- `source`: در این endpoint همیشه از دیتابیس است و معمولا مقدار آن `database` است
- `id`: شناسه داخلی `SoilLocation`
- `lon`: طول جغرافیایی location
- `lat`: عرض جغرافیایی location
- `input_block_count`: تعداد بلوک‌های تعریف‌شده برای این مزرعه
- `farm_boundary`: مرز کل مزرعه به صورت GeoJSON
- `block_layout`: ساختار کلی بلوک‌ها، وضعیت الگوریتم، sub-blockها و metadata سطح مزرعه
- `block_subdivisions`: لیست subdivisionهای سطح بلوک
- `satellite_snapshots`: خلاصه‌های سنجش‌ازدور هر بلوک و هر sub-block

### ساختار هر آیتم `block_subdivisions`

```json
{
  "block_code": "block-1",
  "chunk_size_sqm": 900,
  "grid_points": [],
  "centroid_points": [],
  "grid_point_count": 0,
  "centroid_count": 0,
  "elbow_plot": null,
  "status": "defined",
  "metadata": {},
  "created_at": "2026-05-13T14:00:00Z",
  "updated_at": "2026-05-13T14:00:00Z"
}
```

توضیح:

- `block_code`: کد بلوک
- `chunk_size_sqm`: اندازه هر سلول تحلیل
- `grid_points`: نقاط grid تولیدشده
- `centroid_points`: centroidهای grid
- `grid_point_count`: تعداد نقاط grid
- `centroid_count`: تعداد centroidها
- `elbow_plot`: تصویر elbow plot اگر ساخته شده باشد
- `status`: وضعیت subdivision مثل `defined`، `created`، `subdivided`
- `metadata`: داده‌های تکمیلی

### `400`

وقتی `lat` یا `lon` نامعتبر باشد:

```json
{
  "code": 400,
  "msg": "داده نامعتبر.",
  "data": {
    "lat": ["..."],
    "lon": ["..."]
  }
}
```

### `404`

وقتی location پیدا نشود:

```json
{
  "code": 404,
  "msg": "location پیدا نشد.",
  "data": null
}
```

## 3) `POST /api/location-data/`

کاربرد:

- ثبت یا به‌روزرسانی مزرعه
- ثبت مرز مزرعه
- ثبت بلوک‌های کشاورز

### response موفق `200`

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "source": "created",
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

### توضیح `source`

- `created`: این location تازه ساخته شده
- `database`: location از قبل وجود داشته و فقط update شده یا همان داده قبلی برگشته

### `400`

حالت اول: body نامعتبر باشد:

```json
{
  "code": 400,
  "msg": "داده نامعتبر.",
  "data": {
    "farm_boundary": ["مختصات گوشه‌های کل زمین باید ارسال شود."]
  }
}
```

حالت دوم: مرز کل مزرعه نه در request آمده و نه قبلا ذخیره شده:

```json
{
  "code": 400,
  "msg": "داده نامعتبر.",
  "data": {
    "farm_boundary": [
      "برای ثبت location باید گوشه‌های کل زمین ارسال یا قبلاً ذخیره شده باشد."
    ]
  }
}
```

## 4) `POST /api/location-data/ndvi-health/`

کاربرد:

- برگرداندن وضعیت سلامت پوشش گیاهی مزرعه بر اساس NDVI

### response موفق `200`

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

### توضیح فیلدها

- `ndviIndex`: شاخص اصلی NDVI برای UI
- `mean_ndvi`: میانگین NDVI محاسبه‌شده
- `ndvi_map`: داده نقشه یا لایه NDVI
- `vegetation_health_class`: کلاس سلامت پوشش گیاهی
- `observation_date`: تاریخ مشاهده
- `satellite_source`: منبع داده ماهواره‌ای
- `healthData`: کارت‌های خلاصه برای نمایش در فرانت

### ساختار هر آیتم `healthData`

- `title`: عنوان آیتم
- `value`: مقدار عددی یا ساختار JSON
- `color`: رنگ پیشنهادی UI
- `icon`: آیکون پیشنهادی UI

### `400`

```json
{
  "code": 400,
  "msg": "داده نامعتبر.",
  "data": {
    "farm_uuid": ["..."]
  }
}
```

### `404`

```json
{
  "code": 404,
  "msg": "مزرعه پیدا نشد.",
  "data": null
}
```

## 5) `GET /api/location-data/remote-sensing/`

کاربرد:

- فقط نتایج cache شده remote sensing و subdivision را می‌خواند
- هیچ پردازش جدیدی اجرا نمی‌کند

### response موفق `200`

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "status": "success",
    "source": "database",
    "location": {},
    "block_code": "",
    "chunk_size_sqm": 900,
    "temporal_extent": {
      "start_date": "2026-04-12",
      "end_date": "2026-05-12"
    },
    "summary": {
      "cell_count": 12,
      "ndvi_mean": 0.54,
      "ndwi_mean": 0.21,
      "soil_vv_db_mean": -8.92
    },
    "cells": [],
    "run": {},
    "subdivision_result": {},
    "pagination": {},
    "metadata": {
      "farm_uuid": "11111111-1111-1111-1111-111111111111",
      "cache_hit": true
    }
  }
}
```

### حالت‌های مهم `status`

- `success`: داده کامل در DB موجود است
- `processing`: run در حال انجام است و هنوز observation نهایی کامل نشده
- `not_found`: runی وجود داشته ولی observation قابل استفاده برنگشته

### توضیح فیلدها

- `status`: وضعیت نتیجه
- `source`: معمولا `database` یا `processing`
- `location`: همان ساختار `SoilLocationResponse`
- `block_code`: برای full farm معمولا رشته خالی `""`
- `chunk_size_sqm`: اندازه سلول تحلیل
- `temporal_extent.start_date`: شروع بازه تحلیل
- `temporal_extent.end_date`: پایان بازه تحلیل
- `summary`: خلاصه آماری observationها
- `cells`: observationهای صفحه فعلی
- `run`: اطلاعات run مرتبط
- `subdivision_result`: نتیجه clustering و KMeans
- `pagination`: اطلاعات صفحه‌بندی `cells` و گاهی `assignments`
- `metadata.cache_hit`: نشان می‌دهد پاسخ از cache/DB آمده

### ساختار `summary`

- `cell_count`: تعداد سلول‌ها
- `ndvi_mean`: میانگین NDVI
- `ndwi_mean`: میانگین NDWI
- `soil_vv_db_mean`: میانگین `soil_vv_db`

### ساختار هر آیتم `cells`

```json
{
  "cell_code": "cell-1",
  "block_code": "",
  "chunk_size_sqm": 900,
  "centroid_lat": "35.689500",
  "centroid_lon": "51.389500",
  "geometry": {},
  "temporal_start": "2026-04-12",
  "temporal_end": "2026-05-12",
  "ndvi": 0.61,
  "ndwi": 0.22,
  "soil_vv": 0.13,
  "soil_vv_db": -8.860566,
  "metadata": {}
}
```

### ساختار `run`

```json
{
  "id": 10,
  "block_code": "",
  "chunk_size_sqm": 900,
  "temporal_start": "2026-04-12",
  "temporal_end": "2026-05-12",
  "status": "success",
  "status_label": "completed",
  "pipeline_status": "completed",
  "stage": "completed",
  "selected_features": ["ndvi", "ndwi", "soil_vv_db"],
  "requested_cluster_count": null,
  "metadata": {},
  "error_message": "",
  "started_at": null,
  "finished_at": null,
  "created_at": "2026-05-13T14:00:00Z",
  "updated_at": "2026-05-13T14:00:00Z"
}
```

### ساختار `subdivision_result`

```json
{
  "id": 5,
  "block_code": "",
  "chunk_size_sqm": 900,
  "temporal_start": "2026-04-12",
  "temporal_end": "2026-05-12",
  "cluster_count": 3,
  "selected_features": ["ndvi", "ndwi", "soil_vv_db"],
  "skipped_cell_codes": [],
  "metadata": {},
  "available_k_options": [],
  "cluster_blocks": [],
  "assignments": [],
  "created_at": "2026-05-13T14:00:00Z",
  "updated_at": "2026-05-13T14:00:00Z"
}
```

### ساختار هر `assignment`

```json
{
  "cell_code": "cell-1",
  "cluster_label": 0,
  "centroid_lat": "35.689500",
  "centroid_lon": "51.389500",
  "raw_feature_values": {
    "ndvi": 0.61
  },
  "scaled_feature_values": {
    "ndvi": 0.21
  }
}
```

### ساختار هر `cluster_block`

```json
{
  "uuid": "11111111-1111-1111-1111-111111111111",
  "sub_block_code": "cluster-0",
  "cluster_label": 0,
  "chunk_size_sqm": 900,
  "centroid_lat": "35.689500",
  "centroid_lon": "51.389500",
  "center_cell_code": "cell-1",
  "center_cell_lat": "35.689500",
  "center_cell_lon": "51.389500",
  "cell_count": 4,
  "cell_codes": ["cell-1", "cell-2"],
  "geometry": {},
  "metadata": {},
  "created_at": "2026-05-13T14:00:00Z",
  "updated_at": "2026-05-13T14:00:00Z"
}
```

### `400`

```json
{
  "code": 400,
  "msg": "داده نامعتبر.",
  "data": {
    "farm_uuid": ["..."]
  }
}
```

### `404`

```json
{
  "code": 404,
  "msg": "location پیدا نشد.",
  "data": null
}
```

## 6) `POST /api/location-data/remote-sensing/`

کاربرد:

- اجرای async تحلیل سنجش‌ازدور
- ساخت run و task قابل polling
- اگر داده قبلا در DB موجود باشد هم یک `task_id` tracking برمی‌گرداند تا status بلافاصله نتیجه را بدهد

### response موفق `202`

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

### دو حالت مهم

#### حالت اول: واقعا task جدید ساخته شده

- `status = processing`
- `source = processing`
- `task_id` مربوط به Celery run جدید است

#### حالت دوم: data از قبل در DB وجود دارد

- باز هم `202` برمی‌گردد
- `status` ممکن است `success` باشد
- `source` معمولا `database` است
- `task_id` برای polling ساخته می‌شود
- `GET /runs/{run_id}/status/` بلافاصله نتیجه کامل را می‌دهد

### `400`

```json
{
  "code": 400,
  "msg": "داده نامعتبر.",
  "data": {
    "farm_uuid": ["..."]
  }
}
```

### `404`

```json
{
  "code": 404,
  "msg": "location پیدا نشد.",
  "data": null
}
```

## 7) `GET /api/location-data/remote-sensing/cluster-blocks/{cluster_uuid}/live/`

کاربرد:

- دریافت metricهای زنده یا cache شده برای یک cluster block

### response موفق `200`

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "status": "success",
    "source": "database",
    "cluster_block": {},
    "temporal_extent": {
      "start_date": "2026-04-12",
      "end_date": "2026-05-12"
    },
    "selected_features": ["ndvi", "ndwi", "soil_vv_db"],
    "summary": {
      "cell_count": 2,
      "ndvi_mean": 0.54,
      "ndwi_mean": 0.17,
      "soil_vv_db_mean": -9.0
    },
    "metrics": {
      "ndvi": 0.54,
      "ndwi": 0.17,
      "soil_vv": 0.14,
      "soil_vv_db": -9.0
    },
    "metadata": {
      "requested_cluster_uuid": "11111111-1111-1111-1111-111111111111",
      "cache_hit": true
    }
  }
}
```

### توضیح فیلدها

- `source`: اگر از observationهای DB آمده باشد `database` و اگر مستقیم از openEO آمده باشد `openeo`
- `cluster_block`: ساختار کامل sub-block
- `selected_features`: metricهایی که برای تحلیل استفاده می‌شوند
- `summary`: خلاصه آماری cluster
- `metrics`: metric تجمیع‌شده همان cluster
- `metadata`: اطلاعات تکمیلی مثل backend، source_result_id، source_run_id

### `400`

- پارامترهای تاریخ نامعتبر باشند
- یا هندسه cluster معتبر نباشد

نمونه:

```json
{
  "code": 400,
  "msg": "هندسه زیر‌بلاک KMeans نامعتبر است.",
  "data": {
    "cluster_uuid": ["11111111-1111-1111-1111-111111111111"]
  }
}
```

### `404`

```json
{
  "code": 404,
  "msg": "زیر‌بلاک KMeans پیدا نشد.",
  "data": null
}
```

### `502`

وقتی openEO پاسخ ندهد:

```json
{
  "code": 502,
  "msg": "خواندن داده از openEO ناموفق بود.",
  "data": {
    "detail": "..."
  }
}
```

## 8) `GET /api/location-data/remote-sensing/cluster-recommendations/`

کاربرد:

- مقایسه گیاه‌های ثبت‌شده در `farm_data`
- استفاده از داده کلاسترها
- استفاده از `crop_simulation`
- پیشنهاد بهترین گیاه برای هر cluster

### response موفق `200`

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "farm_uuid": "11111111-1111-1111-1111-111111111111",
    "location_id": 12,
    "evaluated_plant_count": 2,
    "cluster_count": 2,
    "registered_plants": [],
    "clusters": [],
    "source_metadata": {}
  }
}
```

### توضیح فیلدهای سطح بالا

- `farm_uuid`: شناسه مزرعه
- `location_id`: شناسه داخلی location
- `evaluated_plant_count`: تعداد گیاه‌هایی که وارد simulation شده‌اند
- `cluster_count`: تعداد clusterهای بررسی‌شده
- `registered_plants`: گیاه‌های ثبت‌شده روی مزرعه
- `clusters`: خروجی نهایی هر cluster
- `source_metadata`: metadata کلی پاسخ

### ساختار هر آیتم `registered_plants`

```json
{
  "plant_id": 101,
  "plant_name": "Tomato",
  "position": 0,
  "stage": "vegetative"
}
```

### ساختار هر آیتم `clusters`

```json
{
  "block_code": "block-1",
  "cluster_uuid": "11111111-1111-1111-1111-111111111111",
  "sub_block_code": "cluster-0",
  "cluster_label": 0,
  "temporal_extent": {
    "start_date": "2026-04-12",
    "end_date": "2026-05-12"
  },
  "cluster_block": {},
  "satellite_metrics": {
    "ndvi": 0.51,
    "ndwi": 0.24,
    "soil_vv": 0.13
  },
  "sensor_metrics": {},
  "resolved_metrics": {
    "ndvi": 0.51,
    "ndwi": 0.24,
    "soil_vv": 0.13
  },
  "candidate_plants": [],
  "suggested_plant": {},
  "source_metadata": {}
}
```

### ساختار هر آیتم `candidate_plants`

```json
{
  "plant_id": 101,
  "plant_name": "Tomato",
  "position": 0,
  "stage": "vegetative",
  "score": 150.0,
  "predicted_yield": 150.0,
  "predicted_yield_tons": 0.15,
  "biomass": 300.0,
  "max_lai": 4.2,
  "simulation_engine": "pcse",
  "simulation_model_name": "Wofost81_NWLP_CWB_CNB",
  "simulation_warning": null,
  "supporting_metrics": {}
}
```

### `400`

وقتی مزرعه گیاه ثبت‌شده نداشته باشد یا پیش‌نیاز simulation کامل نباشد:

```json
{
  "code": 400,
  "msg": "برای این مزرعه هنوز هیچ گیاهی در farm_data ثبت نشده است.",
  "data": null
}
```

### `404`

وقتی مزرعه یا خروجی KMeans پیدا نشود:

```json
{
  "code": 404,
  "msg": "برای این مزرعه هنوز خروجی KMeans در location_data ثبت نشده است.",
  "data": null
}
```

## 9) `GET /api/location-data/remote-sensing/results/{result_id}/k-options/`

کاربرد:

- لیست همه Kهای ذخیره‌شده برای یک subdivision result

### response موفق `200`

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

### توضیح فیلدها

- `result_id`: شناسه subdivision result
- `active_requested_k`: K فعال فعلی
- `recommended_requested_k`: K پیشنهادی سیستم
- `options`: لیست کامل گزینه‌ها

### ساختار هر آیتم `options`

```json
{
  "id": 11,
  "requested_k": 3,
  "effective_cluster_count": 3,
  "is_active": true,
  "is_recommended": false,
  "selection_source": "user",
  "metadata": {},
  "cluster_blocks": [],
  "created_at": "2026-05-13T14:00:00Z",
  "updated_at": "2026-05-13T14:00:00Z"
}
```

### ساختار هر `cluster_blocks` داخل option

```json
{
  "cluster_label": 0,
  "sub_block_code": "cluster-0",
  "chunk_size_sqm": 900,
  "centroid_lat": "35.689500",
  "centroid_lon": "51.389500",
  "center_cell_code": "cell-1",
  "center_cell_lat": "35.689500",
  "center_cell_lon": "51.389500",
  "cell_count": 4,
  "cell_codes": ["cell-1", "cell-2"],
  "geometry": {},
  "metadata": {}
}
```

### `404`

```json
{
  "code": 404,
  "msg": "subdivision result پیدا نشد.",
  "data": null
}
```

## 10) `POST /api/location-data/remote-sensing/results/{result_id}/k-options/activate/`

کاربرد:

- فعال‌سازی یکی از Kهای ذخیره‌شده

### response موفق `200`

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "result_id": 5,
    "activated_requested_k": 4,
    "subdivision_result": {}
  }
}
```

### توضیح فیلدها

- `result_id`: شناسه result
- `activated_requested_k`: K که الان active شده
- `subdivision_result`: خروجی کامل subdivision بعد از sync شدن روی K جدید

### `400`

حالت اول: body نامعتبر

```json
{
  "code": 400,
  "msg": "داده نامعتبر.",
  "data": {
    "requested_k": ["..."]
  }
}
```

حالت دوم: K داخل optionها وجود ندارد

```json
{
  "code": 400,
  "msg": "K انتخابی برای این subdivision result موجود نیست.",
  "data": {
    "requested_k": [7]
  }
}
```

### `404`

```json
{
  "code": 404,
  "msg": "subdivision result پیدا نشد.",
  "data": null
}
```

## 11) `GET /api/location-data/remote-sensing/runs/{run_id}/status/`

کاربرد:

- polling وضعیت run
- دیدن stageهای pipeline
- اگر run کامل شده باشد، دیدن نتیجه نهایی
- اگر run از نوع cache-hit باشد، دیدن نتیجه کامل DB بلافاصله

### response موفق `200` در حالت pending/running

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "status": "running",
    "source": "database",
    "run": {},
    "task_id": "11111111-1111-1111-1111-111111111111",
    "task": {
      "current_stage": "fetching_remote_metrics",
      "current_stage_details": {},
      "timestamps": {},
      "stages": [],
      "metric_progress": {},
      "celery": {
        "state": "STARTED",
        "ready": false,
        "successful": false,
        "failed": false,
        "info": {}
      }
    }
  }
}
```

### response موفق `200` در حالت completed

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "status": "completed",
    "source": "database",
    "run": {},
    "task_id": "11111111-1111-1111-1111-111111111111",
    "task": {
      "current_stage": "completed",
      "current_stage_details": {},
      "timestamps": {},
      "stages": []
    },
    "location": {},
    "block_code": "",
    "chunk_size_sqm": 900,
    "temporal_extent": {
      "start_date": "2026-04-12",
      "end_date": "2026-05-12"
    },
    "summary": {
      "cell_count": 12,
      "ndvi_mean": 0.54,
      "ndwi_mean": 0.21,
      "soil_vv_db_mean": -8.92
    },
    "cells": [],
    "subdivision_result": {},
    "pagination": {}
  }
}
```

### توضیح فیلدهای `task`

- `current_stage`: stage فعلی pipeline
- `current_stage_details`: جزئیات همان stage
- `timestamps`: زمان ورود به stageها
- `stages`: تاریخچه stageها
- `metric_progress`: پیشرفت metricها هنگام fetch داده
- `retry`: اطلاعات retry اگر task در حال retry باشد
- `last_error`: آخرین خطا
- `failure_reason`: علت fail شدن task
- `celery.state`: وضعیت Celery مثل `PENDING`، `STARTED`، `RETRY`
- `celery.ready`: آیا task تمام شده
- `celery.successful`: آیا task موفق بوده
- `celery.failed`: آیا task fail شده
- `celery.info`: اطلاعات خام Celery

### مقادیر متداول `status`

- `pending`
- `running`
- `retrying`
- `completed`
- `failed`

### `404`

```json
{
  "code": 404,
  "msg": "run با این task_id پیدا نشد.",
  "data": null
}
```

## 12) نکات مهم برای فرانت

- در همه endpointها اول `code` و بعد `data` را چک کنید.
- در `POST /remote-sensing/` همیشه انتظار `task_id` داشته باشید.
- در `POST /remote-sensing/` اگر داده قبلا موجود باشد هم ممکن است `202` بگیرید، چون سیستم برای polling یک run قابل پیگیری می‌سازد.
- در `GET /remote-sensing/runs/{run_id}/status/` اگر `status = completed` شد، همان response نهایی را استفاده کنید و دیگر لازم نیست `GET /remote-sensing/` را دوباره صدا بزنید.
- در `GET /remote-sensing/cluster-blocks/{cluster_uuid}/live/` مقدار `source` مهم است:
  - `database`: از cache
  - `openeo`: از backend زنده
- در responseهای subdivision، pagination ممکن است هم برای `cells` باشد و هم برای `assignments`.

## 13) محل فایل

این مستند در این مسیر ذخیره شده است:

- `docs/location_data_api_responses_fa.md`
