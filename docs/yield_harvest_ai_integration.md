# مرجع کامل ارتباط Backend با AI در ماژول Yield & Harvest

این سند قرارداد فعلی backend برای endpointهای ماژول `yield_harvest` را توضیح می‌دهد؛ هم از دید فرانت/کاربر، هم از دید payload ارسالی به سرویس AI.

این سند این endpointها را پوشش می‌دهد:

- `POST /api/yield-harvest/current-farm-chart/`
- `POST /api/yield-harvest/growth/`
- `GET /api/yield-harvest/growth/{task_id}/status/`
- `POST /api/yield-harvest/harvest-prediction/`
- `POST /api/yield-harvest/yield-prediction/`
- `GET /api/yield-harvest/yield-harvest-summary/`

---

## هدف این سند

این ماژول باید برای endpointهای farm-based تا حد ممکن فقط `farm_uuid` را از کاربر بگیرد و بقیه context لازم را خودش از دیتابیس بخواند.

مهم‌ترین قاعده این سند:

- فرانت نباید `plant_name` را برای endpointهای farm-based ارسال کند.
- backend باید `plant_name` را از `farm_hub.models.FarmHub` استخراج کند.
- منبع استخراج `plant_name` این است:
  1. اولین محصول `farm.products` بر اساس `id`
  2. اگر مزرعه محصول نداشت، اولین محصول `farm.farm_type.products` بر اساس `id`

پیاده‌سازی فعلی این رفتار در فایل زیر است:

- `yield_harvest/views.py`

مدل‌های منبع داده:

- `farm_hub/models.py`

---

## احراز هویت و سطح دسترسی

همه endpointهای این سند نیاز به JWT معتبر دارند.

### هدرهای متداول

```http
Authorization: Bearer <access_token>
Content-Type: application/json
Accept: application/json
```

### اعتبارسنجی مالکیت مزرعه

برای endpointهایی که `farm_uuid` می‌گیرند، backend فقط زمانی درخواست را قبول می‌کند که:

- مزرعه وجود داشته باشد
- و مالک آن مزرعه همان `request.user` باشد

اگر مزرعه برای کاربر جاری پیدا نشود:

```json
{
  "code": 404,
  "msg": "error",
  "data": {
    "farm_uuid": ["Farm not found."]
  }
}
```

---

## الگوی کلی پاسخ‌ها

تقریباً تمام endpointهای این ماژول از envelope زیر استفاده می‌کنند:

```json
{
  "code": 200,
  "msg": "success",
  "data": {}
}
```

### معنی فیلدهای envelope

| فیلد | نوع | توضیح |
|---|---|---|
| `code` | integer | کد منطقی پاسخ؛ معمولاً با HTTP status هم‌راستا است |
| `msg` | string | پیام کوتاه پاسخ |
| `data` | object / array / null | بدنه اصلی پاسخ |

### خطاهای متداول

| HTTP Status | `code` | توضیح |
|---|---|---|
| `400` | `400` | ورودی نامعتبر است |
| `404` | `404` | مزرعه برای کاربر جاری پیدا نشد |
| `500` | `500` | AI یا لایه محاسباتی upstream خطا داده است |
| `202` | `202` | تسک async با موفقیت در صف قرار گرفته است |

---

## قرارداد ورودی از دید Frontend

### اصل طراحی

برای endpointهای farm-based این ماژول، فرانت فقط باید `farm_uuid` را ارسال کند و نباید موارد زیر را از کاربر بگیرد:

- `plant_name`
- `crop_name` برای جریان‌های farm-based prediction
- هر context دیگری که backend می‌تواند از مزرعه استخراج کند

### استثناها

- `GET /api/yield-harvest/growth/{task_id}/status/` به `farm_uuid` نیاز ندارد؛ چون بر اساس `task_id` کار می‌کند.
- `GET /api/yield-harvest/yield-harvest-summary/` علاوه بر `farm_uuid` می‌تواند queryهای اختیاری هم داشته باشد، ولی در قرارداد فرانت ساده می‌توان فقط `farm_uuid` را فرستاد.
- endpoint رشد (`growth`) در لایه AI پارامترهای پیشرفته دارد، اما در قرارداد ساده frontend این سند، ورودی کاربر باید فقط `farm_uuid` باشد و backend باید context گیاه را از مزرعه بردارد.

---

## نگاشت endpointهای Backend به AI

| Backend Route | Method | AI Route | Method |
|---|---|---|---|
| `/api/yield-harvest/current-farm-chart/` | `POST` | `/api/crop-simulation/current-farm-chart/` | `POST` |
| `/api/yield-harvest/growth/` | `POST` | `/api/crop-simulation/growth/` | `POST` |
| `/api/yield-harvest/growth/{task_id}/status/` | `GET` | `/api/crop-simulation/growth/{task_id}/status/` | `GET` |
| `/api/yield-harvest/harvest-prediction/` | `POST` | `/api/crop-simulation/harvest-prediction/` | `POST` |
| `/api/yield-harvest/yield-prediction/` | `POST` | `/api/crop-simulation/yield-prediction/` | `POST` |
| `/api/yield-harvest/yield-harvest-summary/` | `GET` | `/api/crop-simulation/yield-harvest-summary/` | `GET` |

---

## منبع `plant_name` در Backend

### منبع داده

backend نام گیاه را از مدل `FarmHub` در `farm_hub/models.py` می‌گیرد.

### ترتیب انتخاب

1. `farm.products.order_by("id").first()`
2. اگر مورد 1 خالی بود: `farm.farm_type.products.order_by("id").first()`

### مثال مفهومی

اگر مزرعه این محصولات را داشته باشد:

```text
farm.products = ["خیار", "گوجه‌فرنگی"]
```

backend این مقدار را برای AI می‌فرستد:

```json
{
  "farm_uuid": "11111111-1111-1111-1111-111111111111",
  "plant_name": "خیار"
}
```

یعنی معیار فعلی، «اولین محصول بر اساس `id`» است، نه محصول انتخاب‌شده توسط کاربر.

---

## 1) POST `/api/yield-harvest/current-farm-chart/`

### کاربرد

دریافت نمودار وضعیت فعلی مزرعه بر اساس شبیه‌سازی رشد محصول.

### ورودی از فرانت

```json
{
  "farm_uuid": "11111111-1111-1111-1111-111111111111"
}
```

### نکته مهم

- `plant_name` از کاربر گرفته نمی‌شود.
- backend آن را از مزرعه استخراج می‌کند.

### payload ارسالی backend به AI

نمونه:

```json
{
  "farm_uuid": "11111111-1111-1111-1111-111111111111",
  "plant_name": "خیار"
}
```

### پاسخ موفق

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "farm_uuid": "11111111-1111-1111-1111-111111111111",
    "plant_name": "گوجه‌فرنگی",
    "engine": "growth_projection",
    "model_name": "growth_projection_v1",
    "scenario_id": 12,
    "simulation_warning": null,
    "categories": ["2026-04-01", "2026-04-02"],
    "series": [
      {
        "name": "تعداد برگ تخمینی",
        "key": "leaf_count_estimate",
        "data": [120.0, 140.0]
      }
    ],
    "summary": [
      {
        "title": "تعداد برگ تخمینی",
        "subtitle": "وضعیت فعلی",
        "amount": 140.0,
        "unit": "leaf",
        "avatarColor": "success",
        "avatarIcon": "tabler-leaf"
      }
    ],
    "current_state": {
      "date": "2026-04-02",
      "leaf_count_estimate": 140.0,
      "leaf_area_index": 0.0117,
      "biomass_weight": 45.0,
      "storage_organ_weight": 10.0,
      "soil_moisture_percent": 41.2,
      "development_stage": 0.35,
      "gdd": 9.0
    },
    "metrics": {
      "yield_estimate": 10.0
    },
    "daily_output": []
  }
}
```

### توضیح فیلدهای پاسخ

| فیلد | نوع | توضیح |
|---|---|---|
| `farm_uuid` | string / null | شناسه مزرعه |
| `plant_name` | string | نام گیاهی که شبیه‌سازی برای آن انجام شده |
| `engine` | string / null | موتور شبیه‌سازی |
| `model_name` | string / null | نام مدل |
| `scenario_id` | integer / null | شناسه سناریو |
| `simulation_warning` | string / null | هشدار غیر بحرانی |
| `categories` | array[string] | محور زمانی نمودار |
| `series` | array[object] | سری‌های نمودار |
| `summary` | array[object] | کارت‌های خلاصه |
| `current_state` | object | وضعیت آخرین روز شبیه‌سازی |
| `metrics` | object | شاخص‌های محاسبه‌شده |
| `daily_output` | array[object] | خروجی خام روزانه |

### توضیح `series[]`

| فیلد | نوع | توضیح |
|---|---|---|
| `name` | string | عنوان سری |
| `key` | string | کلید فنی سری |
| `data` | array[number] | مقادیر سری |

### توضیح `summary[]`

| فیلد | نوع | توضیح |
|---|---|---|
| `title` | string | عنوان کارت |
| `subtitle` | string | زیرعنوان |
| `amount` | number | مقدار اصلی |
| `unit` | string | واحد |
| `avatarColor` | string | رنگ پیشنهادی UI |
| `avatarIcon` | string | آیکن پیشنهادی UI |

### توضیح `current_state`

| فیلد | نوع | توضیح |
|---|---|---|
| `date` | string | تاریخ آخرین رکورد |
| `leaf_count_estimate` | number | تعداد برگ تخمینی |
| `leaf_area_index` | number | شاخص سطح برگ |
| `biomass_weight` | number | وزن بیوماس |
| `storage_organ_weight` | number | وزن اندام ذخیره‌ای / محصول |
| `soil_moisture_percent` | number | درصد رطوبت خاک |
| `development_stage` | number | مرحله رشد |
| `gdd` | number | درجه-روز رشد |

---

## 2) POST `/api/yield-harvest/growth/`

### کاربرد

شروع شبیه‌سازی رشد به صورت async.

### قرارداد ساده فرانت

در قرارداد frontend این سند، فرانت فقط باید `farm_uuid` را بفرستد.

```json
{
  "farm_uuid": "11111111-1111-1111-1111-111111111111"
}
```

### نکته مهم

- `plant_name` نباید از کاربر گرفته شود.
- backend آن را از مزرعه استخراج می‌کند.
- `task_id` خروجی این endpoint، ورودی endpoint وضعیت است.

### payload ارسالی backend به AI

نمونه مفهومی:

```json
{
  "farm_uuid": "11111111-1111-1111-1111-111111111111",
  "plant_name": "خیار",
  "dynamic_parameters": ["DVS", "LAI", "TAGP", "TWSO", "SM"]
}
```

نکته: upstream AI ممکن است پارامترهای پیشرفته بیشتری هم بپذیرد، ولی این‌ها نباید از کاربر نهایی گرفته شوند مگر این‌که قرارداد جداگانه‌ای برای expert mode تعریف شود.

### پاسخ موفق

```json
{
  "code": 202,
  "msg": "تسک شبیه سازی رشد در صف قرار گرفت.",
  "data": {
    "task_id": "growth-task-1",
    "status_url": "/api/crop-simulation/growth/growth-task-1/status/",
    "plant_name": "گوجه‌فرنگی"
  }
}
```

### توضیح فیلدهای پاسخ

| فیلد | نوع | توضیح |
|---|---|---|
| `task_id` | string | شناسه تسک |
| `status_url` | string | آدرس بررسی وضعیت تسک |
| `plant_name` | string | نام گیاهی که شبیه‌سازی برای آن آغاز شده |

---

## 3) GET `/api/yield-harvest/growth/{task_id}/status/`

### کاربرد

بررسی وضعیت و نتیجه تسک async شبیه‌سازی رشد.

### ورودی

این endpoint از کاربر `farm_uuid` نمی‌گیرد.

### Path Parameter

| فیلد | نوع | اجباری | توضیح |
|---|---|---:|---|
| `task_id` | string | بله | شناسه تسک برگشتی از endpoint رشد |

### Query اختیاری

| فیلد | نوع | اجباری | توضیح |
|---|---|---:|---|
| `page` | integer | خیر | شماره صفحه stageها |
| `page_size` | integer | خیر | تعداد آیتم در هر صفحه |

### پاسخ در حالت `PENDING`

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "task_id": "growth-task-1",
    "status": "PENDING",
    "message": "تسک در صف یا یافت نشد."
  }
}
```

### پاسخ در حالت `PROGRESS`

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "task_id": "growth-task-1",
    "status": "PROGRESS",
    "progress": {
      "current": 2,
      "total": 3,
      "percent": 66.7
    }
  }
}
```

### پاسخ در حالت `SUCCESS`

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "task_id": "growth-task-1",
    "status": "SUCCESS",
    "result": {
      "plant_name": "گوجه‌فرنگی",
      "dynamic_parameters": ["DVS"],
      "engine": "growth_projection",
      "model_name": "growth_projection_v1",
      "scenario_id": null,
      "simulation_warning": null,
      "summary_metrics": {},
      "stage_timeline": [],
      "stages_page": [],
      "pagination": {
        "page": 1,
        "page_size": 10,
        "total_items": 0,
        "total_pages": 0,
        "has_next": false,
        "has_previous": false
      },
      "daily_records_count": 0,
      "default_page_size": 10
    }
  }
}
```

### پاسخ در حالت `FAILURE`

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "task_id": "growth-task-1",
    "status": "FAILURE",
    "error": "task crashed"
  }
}
```

### توضیح فیلدهای status response

| فیلد | نوع | توضیح |
|---|---|---|
| `task_id` | string | شناسه تسک |
| `status` | string | وضعیت تسک: `PENDING`, `PROGRESS`, `SUCCESS`, `FAILURE` |
| `message` | string | پیام کمکی در برخی وضعیت‌ها |
| `progress` | object | وضعیت پیشرفت |
| `result` | object | نتیجه نهایی در حالت موفق |
| `error` | string | خطای نهایی در حالت failure |

### توضیح `progress`

| فیلد | نوع | توضیح |
|---|---|---|
| `current` | integer | مرحله فعلی |
| `total` | integer | کل مراحل |
| `percent` | float | درصد پیشرفت |

### توضیح `result`

| فیلد | نوع | توضیح |
|---|---|---|
| `plant_name` | string | نام گیاه |
| `dynamic_parameters` | array[string] | پارامترهای دینامیک |
| `engine` | string / null | موتور شبیه‌سازی |
| `model_name` | string / null | نام مدل |
| `scenario_id` | integer / null | شناسه سناریو |
| `simulation_warning` | string / null | هشدار محاسباتی |
| `summary_metrics` | object | شاخص‌های خلاصه |
| `stage_timeline` | array[object] | timeline کامل مراحل |
| `stages_page` | array[object] | آیتم‌های همین صفحه |
| `pagination` | object | اطلاعات صفحه‌بندی |
| `daily_records_count` | integer | تعداد رکوردهای روزانه |
| `default_page_size` | integer | اندازه صفحه پیش‌فرض |

### توضیح `pagination`

| فیلد | نوع | توضیح |
|---|---|---|
| `page` | integer | صفحه فعلی |
| `page_size` | integer | اندازه صفحه |
| `total_items` | integer | تعداد کل stageها |
| `total_pages` | integer | تعداد کل صفحه‌ها |
| `has_next` | boolean | آیا صفحه بعدی وجود دارد |
| `has_previous` | boolean | آیا صفحه قبلی وجود دارد |

---

## 4) POST `/api/yield-harvest/harvest-prediction/`

### کاربرد

پیش‌بینی زمان برداشت برای مزرعه.

### ورودی از فرانت

```json
{
  "farm_uuid": "11111111-1111-1111-1111-111111111111"
}
```

### payload ارسالی backend به AI

```json
{
  "farm_uuid": "11111111-1111-1111-1111-111111111111",
  "plant_name": "خیار"
}
```

### پاسخ موفق

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "date": "2026-05-14",
    "dateFormatted": "14 May 2026",
    "daysUntil": 43,
    "description": "شبيه ساز نشان مي دهد حدود 43 روز ديگر تا برداشت باقي مانده است.",
    "optimalWindowStart": "2026-05-11",
    "optimalWindowEnd": "2026-05-17",
    "gddDetails": {
      "current_cumulative_gdd": 50.0,
      "required_gdd_for_maturity": 1200.0,
      "remaining_gdd": 1150.0,
      "simulation_engine": "growth_projection"
    }
  }
}
```

### توضیح فیلدهای پاسخ

| فیلد | نوع | توضیح |
|---|---|---|
| `date` | string | تاریخ تخمینی برداشت به فرمت ISO |
| `dateFormatted` | string | تاریخ قابل نمایش |
| `daysUntil` | integer | تعداد روزهای باقیمانده |
| `description` | string | توضیح متنی |
| `optimalWindowStart` | string | شروع پنجره مناسب برداشت |
| `optimalWindowEnd` | string | پایان پنجره مناسب برداشت |
| `gddDetails` | object | جزئیات محاسبات GDD |

### توضیح `gddDetails`

| فیلد | نوع | توضیح |
|---|---|---|
| `current_cumulative_gdd` | number | GDD تجمعی فعلی |
| `required_gdd_for_maturity` | number | GDD مورد نیاز برای بلوغ |
| `remaining_gdd` | number | GDD باقی‌مانده |
| `estimated_days_to_harvest` | integer | روزهای برآوردی تا برداشت |
| `predicted_harvest_date` | string | تاریخ برآوردی برداشت |
| `predicted_harvest_window` | object | بازه برداشت |
| `daily_gdd_forecast` | array[object] | پیش‌بینی روزانه GDD |
| `simulation_engine` | string | موتور شبیه‌سازی |
| `simulation_model_name` | string | نام مدل |
| `simulation_warning` | string / null | هشدار محاسباتی |
| `scenario_id` | integer / null | شناسه سناریو |

---

## 5) POST `/api/yield-harvest/yield-prediction/`

### کاربرد

پیش‌بینی عملکرد مزرعه.

### ورودی از فرانت

```json
{
  "farm_uuid": "11111111-1111-1111-1111-111111111111"
}
```

### payload ارسالی backend به AI

```json
{
  "farm_uuid": "11111111-1111-1111-1111-111111111111",
  "plant_name": "خیار"
}
```

### پاسخ موفق

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "farm_uuid": "11111111-1111-1111-1111-111111111111",
    "plant_name": "گوجه‌فرنگی",
    "predictedYieldTons": 5.4,
    "predictedYieldRaw": 5400.0,
    "unit": "تن",
    "sourceUnit": "kg/ha",
    "simulationEngine": "growth_projection",
    "simulationModel": "growth_projection_v1",
    "scenarioId": 12,
    "simulationWarning": null,
    "supportingMetrics": {
      "yield_estimate": 5400.0
    }
  }
}
```

### توضیح فیلدهای پاسخ

| فیلد | نوع | توضیح |
|---|---|---|
| `farm_uuid` | string | شناسه مزرعه |
| `plant_name` | string / null | نام گیاه |
| `predictedYieldTons` | number | عملکرد بر حسب تن |
| `predictedYieldRaw` | number | مقدار خام عملکرد |
| `unit` | string | واحد نمایشی |
| `sourceUnit` | string | واحد منبع |
| `simulationEngine` | string / null | موتور شبیه‌سازی |
| `simulationModel` | string / null | نام مدل شبیه‌سازی |
| `scenarioId` | integer / null | شناسه سناریو |
| `simulationWarning` | string / null | هشدار محاسباتی |
| `supportingMetrics` | object | شاخص‌های پشتیبان |

### توضیح `supportingMetrics`

این object بسته به upstream می‌تواند شامل مواردی مانند این‌ها باشد:

| فیلد | نوع | توضیح |
|---|---|---|
| `yield_estimate` | number | برآورد خام عملکرد |
| `biomass` | number | بیوماس برآوردی |
| `max_lai` | number | بیشترین شاخص سطح برگ |

---

## 6) GET `/api/yield-harvest/yield-harvest-summary/`

### کاربرد

دریافت داشبورد کامل عملکرد و برداشت.

### ورودی ساده از فرانت

```http
GET /api/yield-harvest/yield-harvest-summary/?farm_uuid=11111111-1111-1111-1111-111111111111
```

### Queryهای اختیاری قابل پشتیبانی

| فیلد | نوع | اجباری | توضیح |
|---|---|---:|---|
| `farm_uuid` | UUID | بله | شناسه مزرعه |
| `season_year` | integer | خیر | سال زراعی |
| `crop_name` | string | خیر | نام محصول |
| `include_narrative` | boolean | خیر | در صورت `true` متن‌های توضیحی هم merge می‌شوند |

### نکته قرارداد فرانت

در جریان ساده frontend، ارسال فقط `farm_uuid` کافی است و backend بقیه context لازم را مدیریت می‌کند.

### پاسخ موفق

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "farm_uuid": "11111111-1111-1111-1111-111111111111",
    "season_highlights_card": {},
    "yield_prediction": {},
    "harvest_prediction_card": {},
    "harvest_readiness_zones": {},
    "yield_quality_bands": {},
    "harvest_operations_card": {},
    "yield_prediction_chart": {}
  }
}
```

### توضیح top-level response

| فیلد | نوع | توضیح |
|---|---|---|
| `farm_uuid` | string | شناسه مزرعه |
| `season_highlights_card` | object | خلاصه مهم‌ترین KPIها |
| `yield_prediction` | object | خروجی پیش‌بینی عملکرد |
| `harvest_prediction_card` | object | تاریخ و وضعیت برداشت |
| `harvest_readiness_zones` | object | آمادگی برداشت در zoneها |
| `yield_quality_bands` | object | کیفیت برآوردی محصول |
| `harvest_operations_card` | object | عملیات پیشنهادی برداشت |
| `yield_prediction_chart` | object | نمودار عملکرد و بیوماس |

### توضیح `season_highlights_card`

| فیلد | نوع | توضیح |
|---|---|---|
| `title` | string | عنوان کارت |
| `subtitle` | string | توضیح کوتاه |
| `total_predicted_yield` | number / null | عملکرد پیش‌بینی‌شده |
| `yield_unit` | string | واحد عملکرد |
| `target_harvest_date` | string / null | تاریخ هدف برداشت |
| `days_until_harvest` | integer / null | روز باقی‌مانده |
| `average_readiness` | number / null | میانگین آمادگی |
| `primary_quality_grade` | string / null | گرید کیفیت غالب |
| `estimated_revenue` | number / null | درآمد تخمینی |
| `soil_type` | string / null | نوع خاک |

### توضیح `yield_prediction`

| فیلد | نوع | توضیح |
|---|---|---|
| `predicted_yield_tons` | number | عملکرد بر حسب تن |
| `predicted_yield_raw` | number | عملکرد خام |
| `unit` | string | واحد نمایشی |
| `source_unit` | string | واحد منبع |
| `simulation_engine` | string / null | موتور شبیه‌سازی |
| `simulation_model` | string / null | نام مدل |
| `scenario_id` | integer / null | شناسه سناریو |
| `simulation_warning` | string / null | هشدار شبیه‌سازی |
| `secondary_kpis_estimated` | boolean | آیا KPIهای ثانویه تخمینی‌اند |
| `descriptionSource` | string | منبع توضیح |
| `farm_context` | object | context مزرعه |
| `supporting_metrics` | object | متریک‌های پشتیبان |
| `explanation` | string | توضیح متنی |

### توضیح `harvest_prediction_card`

| فیلد | نوع | توضیح |
|---|---|---|
| `harvest_date` | string | تاریخ ISO برداشت |
| `harvest_date_formatted` | string | تاریخ قابل نمایش |
| `days_until` | integer | روز باقی‌مانده |
| `optimal_window_start` | string | شروع بازه مناسب |
| `optimal_window_end` | string | پایان بازه مناسب |
| `description` | string | توضیح متنی |
| `descriptionSource` | string | منبع توضیح |
| `field_conditions` | object | شرایط فعلی مزرعه |
| `readiness_metrics` | object | جزئیات readiness/GDD |

### توضیح `harvest_readiness_zones`

| فیلد | نوع | توضیح |
|---|---|---|
| `observationDate` | string / null | تاریخ مشاهده |
| `vegetationHealthClass` | string / null | کلاس سلامت پوشش گیاهی |
| `meanNdvi` | number / null | NDVI میانگین |
| `ndviTrend` | number / null | روند NDVI |
| `averageReadiness` | number / null | میانگین آمادگی |
| `zones` | array[object] | فهرست zoneها |
| `source` | string | منبع داده |
| `summary` | string | توضیح خلاصه |

### توضیح هر zone در `zones[]`

| فیلد | نوع | توضیح |
|---|---|---|
| `zoneId` | string | شناسه zone |
| `zoneLabel` | string | نام نمایشی zone |
| `gridPosition` | object / null | موقعیت grid |
| `meanNdvi` | number | NDVI میانگین zone |
| `readiness` | integer | درصد آمادگی |
| `daysUntil` | integer | روز باقی‌مانده |
| `status` | string | وضعیت zone |

### توضیح `yield_quality_bands`

| فیلد | نوع | توضیح |
|---|---|---|
| `source` | string | منبع محاسبه |
| `is_estimated` | boolean | آیا مقادیر تخمینی‌اند |
| `protein_content` | object | درصد پروتئین |
| `moisture_percentage` | object | درصد رطوبت |
| `grade_distribution` | array[object] | توزیع گریدها |
| `primary_quality_grade` | string | گرید غالب |
| `quality_score` | number | امتیاز کیفیت |
| `summary` | string | خلاصه متنی |

### توضیح `harvest_operations_card`

| فیلد | نوع | توضیح |
|---|---|---|
| `stage_label` | string | برچسب مرحله عملیاتی |
| `phase_name` | string | نام فاز رشد |
| `days_until_harvest` | integer | روز باقی‌مانده |
| `current_dvs` | number | DVS فعلی |
| `summary` | string | خلاصه عملیاتی |
| `rules_source` | string | منبع قواعد |
| `field_context` | object | context مزرعه |
| `steps` | array[object] | گام‌های عملیاتی |

### توضیح هر step در `steps[]`

| فیلد | نوع | توضیح |
|---|---|---|
| `key` | string | کلید فنی step |
| `title` | string | عنوان عملیات |
| `status` | string | وضعیت step |
| `is_completed` | boolean | آیا انجام شده |
| `estimated_days` | integer | روز برآوردی |
| `note` | string | توضیح تکمیلی |

### توضیح `yield_prediction_chart`

| فیلد | نوع | توضیح |
|---|---|---|
| `series` | array[object] | سری‌های نمودار |
| `xAxis` | object | تنظیمات محور افقی |
| `meta` | object | متادیتای نمودار |

### توضیح `yield_prediction_chart.series[]`

| فیلد | نوع | توضیح |
|---|---|---|
| `name` | string | نام سری |
| `type` | string | نوع رسم مانند `line` یا `area` |
| `data` | array[[timestamp, value]] | داده‌های نمودار؛ timestamp بر حسب milliseconds |

### توضیح `yield_prediction_chart.meta`

| فیلد | نوع | توضیح |
|---|---|---|
| `unit` | string | واحد داده |
| `simulation_engine` | string | موتور شبیه‌سازی |
| `simulation_model` | string | مدل |
| `scenario_id` | integer / null | شناسه سناریو |
| `simulation_warning` | string / null | هشدار شبیه‌سازی |
| `field_context` | object | context مزرعه |

---

## خطاهای رایج با مثال

### نبودن `farm_uuid`

```json
{
  "code": 400,
  "msg": "error",
  "data": {
    "farm_uuid": ["This field is required."]
  }
}
```

### پیدا نشدن مزرعه برای کاربر جاری

```json
{
  "code": 404,
  "msg": "error",
  "data": {
    "farm_uuid": ["Farm not found."]
  }
}
```

### خطای upstream AI

```json
{
  "code": 500,
  "msg": "error",
  "data": {
    "code": 500,
    "msg": "خطا در پیش بینی عملکرد: Plant not found.",
    "data": null
  }
}
```

نکته: در این وضعیت، envelope بیرونی از backend آمده و object داخلی معمولاً همان پاسخ upstream AI است.

---

## پیش‌فرض Swagger

برای endpointهای body-based این ماژول، `farm_uuid` در Swagger با مقدار پیش‌فرض زیر نمایش داده می‌شود:

```text
11111111-1111-1111-1111-111111111111
```

این رفتار برای endpointهای زیر برقرار است:

- `POST /api/yield-harvest/current-farm-chart/`
- `POST /api/yield-harvest/growth/`
- `POST /api/yield-harvest/harvest-prediction/`
- `POST /api/yield-harvest/yield-prediction/`

---

## جمع‌بندی اجرایی برای فرانت

### چیزی که فرانت باید بفرستد

- برای بیشتر endpointها فقط `farm_uuid`
- برای status فقط `task_id`
- در جریان ساده، `plant_name` هرگز از کاربر گرفته نشود

### چیزی که backend خودش مدیریت می‌کند

- پیدا کردن مزرعه متعلق به کاربر
- استخراج `plant_name` از `farm.products` یا `farm.farm_type.products`
- ارسال payload مناسب به AI
- normalize کردن پاسخ AI در envelope استاندارد backend

### چیزی که فرانت نباید به کاربر بسپارد

- انتخاب دستی `plant_name` در این flow
- ساخت payload مستقیم AI
- تفسیر business ruleهای انتخاب محصول

---

## مسیر فایل

این سند در مسیر زیر نگهداری می‌شود:

`docs/yield_harvest_ai_integration.md`
