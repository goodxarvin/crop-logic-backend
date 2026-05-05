# Farm Dashboard API Reference

این سند، API های `dashboard` را به‌صورت کامل توضیح می‌دهد و برای هر بخش مشخص می‌کند داده از کجا دریافت می‌شود.

## Endpoint ها

### 1) دریافت کارت‌های داشبورد
- **Method:** `GET`
- **Path:** `/api/farm-dashboard/`
- **View:** `dashboard/views.py:118`
- **URL config:** `dashboard/urls.py:5`
- **Query param الزامی:** `farm_uuid`
- **Auth:** `IsAuthenticated`

### 2) دریافت تنظیمات داشبورد
- **Method:** `GET`
- **Path:** `/api/farm-dashboard-config/`
- **View:** `dashboard/views.py:67`
- **URL config:** `dashboard/urls_config.py:5`
- **Query param الزامی:** `farm_uuid`
- **Auth:** `IsAuthenticated`

### 3) ویرایش تنظیمات داشبورد
- **Method:** `PATCH`
- **Path:** `/api/farm-dashboard-config/`
- **View:** `dashboard/views.py:67`
- **Body:** `farm_uuid` + هرکدام از `disabled_card_ids`، `row_order`، `enable_drag_reorder`
- **Auth:** `IsAuthenticated`

## نحوه شناسایی مزرعه
- مزرعه از طریق `farm_uuid` و مالک کاربر لاگین‌شده پیدا می‌شود.
- پیاده‌سازی در `dashboard/views.py:20` و `dashboard/views.py:22` است.
- اگر `farm_uuid` ارسال نشود یا مزرعه برای آن کاربر پیدا نشود، خطای validation برمی‌گردد.

## تنظیمات داشبورد
تنظیمات داشبورد per-farm در دیتابیس ذخیره می‌شود.

### فیلدها
- `disabled_card_ids`: لیست کارت‌های غیرفعال
- `row_order`: ترتیب ردیف‌ها
- `enable_drag_reorder`: فعال/غیرفعال بودن drag reorder

### مدل ذخیره‌سازی
- مدل: `FarmDashboardConfig`
- فایل: `dashboard/models.py:6`
- جدول: `farm_dashboard_configs`

### مقادیر پیش‌فرض
- از `dashboard/defaults.py:4` و `dashboard/defaults.py:30` می‌آید.
- کارت‌های معتبر در `dashboard/defaults.py:16`
- ردیف‌های معتبر در `dashboard/defaults.py:4`

### اعتبارسنجی
- serializer اصلی: `dashboard/serializers.py:6`
- serializer patch: `dashboard/serializers.py:43`
- `disabled_card_ids` فقط باید از `VALID_CARD_IDS` باشد.
- `row_order` باید تمام `VALID_ROW_IDS` را دقیقاً یک‌بار داشته باشد.

## نقطه تجمیع اصلی داده‌ها
تمام کارت‌ها در تابع زیر assemble می‌شوند:
- `dashboard/services.py:85`

این تابع خروجی چند app مختلف را جمع می‌کند و response نهایی dashboard را می‌سازد.

## منبع داده هر کارت

### `farmOverviewKpis`
- **از کجا ساخته می‌شود:** `dashboard/services.py:41`
- **نوع:** aggregator
- **منابع ورودی:**
  - `farmHealthScore` از `crop_health.services.get_crop_health_summary_data`
  - `waterStressIndex` از `water.services.get_water_stress_index_data`
  - `avgSoilMoisture` از `device_hub.services.get_sensor_7_in_1_summary_data`
  - `disease_risk` و `pest_risk` از `pest_detection.services.get_risk_summary_data`
  - `yield_prediction_card` از `yield_harvest.services.get_yield_harvest_summary_data`
- **نکته مهم:** این کارت جدول یا مدل مستقل ندارد؛ از چند سرویس ترکیب می‌شود.

### `farmWeatherCard`
- **از کجا پر می‌شود:** `water/services.py:9`
- **مدل اصلی:** `WeatherForecastLog`
- **فایل مدل:** `water/models.py:8`
- **جدول:** `weather_forecast_logs`
- **منطق:** جدیدترین رکورد هواشناسی برای همان `farm` خوانده می‌شود.

### `farmAlertsTracker`
- **از کجا پر می‌شود:** `farm_alerts/services.py:379`
- **مدل اصلی:** `FarmAlert`
- **فایل مدل:** `farm_alerts/models.py:16`
- **جدول:** `farm_alerts`
- **منطق:** هشدارهای active مزرعه خوانده می‌شوند و از روی آن‌ها summary ساخته می‌شود.
- **نکته:** با اینکه مدل `FarmAlertTrackerSnapshot` هم وجود دارد در `farm_alerts/models.py:76`، endpoint فعلی کارت tracker مستقیم از `FarmAlert` می‌سازد، نه از snapshot.

### `sensorValuesList`
- **از کجا پر می‌شود:** `device_hub/services.py:495`
- **جزء داخلی:** `device_hub/services.py:334`
- **مدل‌ها:**
  - `FarmDevice` در `device_hub/models.py:45`
  - `SensorExternalRequestLog` در `device_hub/models.py:94`
- **جداول:**
  - `farm_sensors`
  - `sensor_external_request_logs`
- **منطق:**
  - اول سنسور اصلی خاک مزرعه پیدا می‌شود.
  - بعد history لاگ‌های همان device خوانده می‌شود.
  - از payload لاگ‌ها، مقادیر سنسورها استخراج می‌شود.

### `sensorRadarChart`
- **از کجا پر می‌شود:** `device_hub/services.py:389`
- **منبع داده:** همان `SensorExternalRequestLog` و `FarmDevice`
- **منطق:** آخرین reading سنسور 7-in-1 گرفته می‌شود و بر اساس ideal range برای هر فیلد score ساخته می‌شود.

### `sensorComparisonChart`
- **از کجا پر می‌شود:** `device_hub/services.py:412`
- **منبع داده:** `SensorExternalRequestLog`
- **منطق:** history چند reading آخر برای رطوبت خاک گرفته می‌شود و series نمودار ساخته می‌شود.

### `anomalyDetectionCard`
- **از کجا پر می‌شود:** `device_hub/services.py:451`
- **منبع داده:** `SensorExternalRequestLog`
- **منطق:** آخرین reading با بازه‌های ideal مقایسه می‌شود و anomaly های out-of-range ساخته می‌شود.
- **نکته:** در app `farm_alerts` یک مدل `AnomalyDetection` در `farm_alerts/models.py:41` هم وجود دارد، اما dashboard فعلی این کارت را از آن مدل نمی‌خواند.

### `farmAlertsTimeline`
- **از کجا پر می‌شود:** `farm_alerts/services.py:410`
- **مدل اصلی:** `FarmAlert`
- **فایل مدل:** `farm_alerts/models.py:16`
- **جدول:** `farm_alerts`
- **منطق:** حداکثر 10 alert آخر مزرعه خوانده می‌شود.

### `waterNeedPrediction`
- **از کجا پر می‌شود:** `water/services.py:58`
- **مدل اصلی:** `IrrigationRecommendationRequest`
- **فایل مدل:** `irrigation/models.py:9`
- **جدول:** `irrigation_requests`
- **منطق:**
  - از `response_payload` آخرین درخواست آبیاری، بخش `water_balance.daily` استخراج می‌شود.
  - سپس `gross_irrigation_mm` ها تبدیل به series نمودار می‌شوند.
- **نکته:** این کارت در app `water` assemble می‌شود ولی source واقعی‌اش داده‌ی persisted آبیاری است.

### `harvestPredictionCard`
- **از کجا پر می‌شود:** `yield_harvest/services.py:7`
- **مدل اصلی:** `YieldHarvestPredictionLog`
- **فایل مدل:** `yield_harvest/models.py:8`
- **جدول:** `yield_harvest_prediction_logs`
- **منطق:** جدیدترین لاگ برداشت/عملکرد مزرعه خوانده می‌شود.

### `yieldPredictionChart`
- **از کجا پر می‌شود:** `yield_harvest/services.py:7`
- **مدل اصلی:** `YieldHarvestPredictionLog`
- **فایل مدل:** `yield_harvest/models.py:8`
- **جدول:** `yield_harvest_prediction_logs`
- **منطق:** `chart_data` از همان لاگ برداشت/عملکرد برگردانده می‌شود.

### `soilMoistureHeatmap`
- **از کجا پر می‌شود:** `device_hub/services.py:469`
- **منبع داده:** `SensorExternalRequestLog`
- **مدل کمکی device:** `FarmDevice`
- **منطق:** چند reading آخر رطوبت خاک به فرمت heatmap/chart تبدیل می‌شود.

### `ndviHealthCard`
- **از کجا پر می‌شود:** `crop_health/services.py:6`
- **منبع داده فعلی:** mock data
- **فایل:** `crop_health/mock_data.py` از طریق `crop_health/services.py:3`
- **منطق:** فعلاً از دیتابیس یا external log خوانده نمی‌شود؛ مستقیم از mock برمی‌گردد.

### `recommendationsList`
- **از کجا ساخته می‌شود:** `dashboard/services.py:54`
- **نوع:** aggregator
- **منابع ورودی:**
  - recommendationهای ذخیره‌شده در `Recommendation` از `farm_alerts/services.py:459`
  - پیشنهاد آبیاری از `irrigation/services.py:289`
  - پیشنهاد کوددهی از `fertilization/services.py:79`
  - بازه برداشت از `yield_harvest.services.get_yield_harvest_summary_data`
- **مدل‌های اصلی:**
  - `Recommendation` در `farm_alerts/models.py:59`
  - `IrrigationRecommendationRequest` در `irrigation/models.py:9`
  - `FertilizationRecommendationRequest` در `fertilization/models.py:9`
  - `YieldHarvestPredictionLog` در `yield_harvest/models.py:8`
- **نکته:** این کارت داده چند domain مختلف را یکی می‌کند و duplicate titleها را حذف می‌کند.

### `economicOverview`
- **از کجا پر می‌شود:** `economic_overview/services.py:7`
- **مدل اصلی:** `EconomicOverviewLog`
- **فایل مدل:** `economic_overview/models.py:8`
- **جدول:** `economic_overview_logs`
- **منطق:** آخرین لاگ اقتصادی مزرعه خوانده می‌شود.

## منابعی که فعلاً mock هستند
این بخش مهم است، چون user خواسته بداند اطلاعات از کجا می‌آید:

- `ndviHealthCard` از mock می‌آید: `crop_health/services.py:6`
- `farmHealthScore` که داخل `farmOverviewKpis` استفاده می‌شود هم از mock می‌آید: `crop_health/services.py:6`
- `disease_risk` و `pest_risk` که داخل `farmOverviewKpis` استفاده می‌شوند از mock می‌آیند: `pest_detection/services.py:6`

## منابعی که از دیتابیس می‌آیند
- تنظیمات dashboard از `FarmDashboardConfig`
- weather از `WeatherForecastLog`
- alerts/timeline از `FarmAlert`
- recommendationهای ذخیره‌شده از `Recommendation`
- داده آبیاری از `IrrigationRecommendationRequest`
- داده کوددهی برای recommendation card از `FertilizationRecommendationRequest`
- برداشت/عملکرد از `YieldHarvestPredictionLog`
- overview اقتصادی از `EconomicOverviewLog`
- سنسورها از `FarmDevice` و `SensorExternalRequestLog`

## وابستگی بین app ها در dashboard
تجمیع dashboard در `dashboard/services.py:85` به این app ها وابسته است:
- `water`
- `crop_health`
- `economic_overview`
- `farm_alerts`
- `fertilization`
- `irrigation`
- `pest_detection`
- `device_hub`
- `yield_harvest`

## نمونه flow برای `GET /api/farm-dashboard/`
1. کاربر `farm_uuid` را می‌فرستد.
2. در `dashboard/views.py:127` مزرعه متعلق به user پیدا می‌شود.
3. `dashboard/services.py:85` صدا زده می‌شود.
4. این تابع به سرویس‌های appهای مختلف call می‌زند.
5. هر سرویس یا از DB می‌خواند یا از mock/template.
6. پاسخ نهایی به‌صورت یک object شامل تمام cardها برمی‌گردد.

## نکات مهم عملی
- endpoint کارت‌ها فقط config را برنمی‌گرداند؛ payload کامل تمام cardها را یکجا برمی‌گرداند.
- config dashboard از خود کارت‌ها جداست و در endpoint جداگانه مدیریت می‌شود.
- بعضی کارت‌ها production data دارند، بعضی transitional هستند، و بعضی هنوز mock دارند.
- اگر برای مزرعه داده‌ای در بعضی جدول‌ها نباشد، معمولاً fallback/template خالی برمی‌گردد.

## فایل‌های مرجع مهم
- `dashboard/views.py:67`
- `dashboard/views.py:118`
- `dashboard/services.py:85`
- `dashboard/defaults.py:4`
- `dashboard/serializers.py:6`
- `dashboard/models.py:6`
- `docs/dashboard_card_service_map.md:1`

