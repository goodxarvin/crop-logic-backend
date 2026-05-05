# نقشه سرویس کارت های داشبورد

این سند مرجع فشرده `وضعیت واقعی کارت های داشبورد` است؛ نه طراحی آینده.  
تمرکز آن روی منبع داده واقعی، status فعلی، و semantics پاسخ در runtime است.

## قانون runtime در برابر seed

- داده seed / bootstrap / fixture مجاز است و باید فقط از مسیرهای seeding و bootstrap در دسترس بماند.
- داده `mock/sample/demo` نباید در مسیر runtime سرویس، view یا adapter برای تولید پاسخ production-like استفاده شود.
- اگر داده واقعی وجود ندارد، سرویس باید `empty state` یا `failure contract` صریح برگرداند، نه داده ساختگی موفق.

## نقطه شروع فعلی

- تجمیع اصلی کارت‌ها در `dashboard/services.py` داخل `get_farm_dashboard_cards` انجام می‌شود.
- endpoint فعلی ارسال کارت‌ها در `dashboard/views.py` داخل `FarmDashboardCardsView` قرار دارد.
- لیست کارت‌های معتبر در `dashboard/defaults.py` داخل `VALID_CARD_IDS` نگهداری می‌شود.

## جمع‌بندی سریع

| Card ID | Status | semantics | منبع اصلی | تابع/سرویس فعلی | app داده | توضیح |
| --- | --- | --- | --- | --- | --- | --- |
| `farmOverviewKpis` | `implemented / transitional` | aggregator | تجمیع چند سرویس | `_build_overview_kpis` | `dashboard` | منبع واحد ندارد |
| `farmWeatherCard` | `partial` | provider/persisted | آب و هوا | `get_farm_weather_card_data` | `water` | نباید fallback ساختگی runtime داشته باشد |
| `farmAlertsTracker` | `implemented` | cached snapshot | snapshot persisted | `get_alert_tracker_data` | `farm_alerts` | live AI نیست |
| `sensorValuesList` | `implemented / transitional` | persisted sensor log | سنسور 7-in-1 | `get_sensor_7_in_1_summary_data` | `sensor_7_in_1` | adoption کامل facade `farm_data` هنوز کامل نشده |
| `sensorRadarChart` | `implemented / transitional` | persisted sensor log | سنسور 7-in-1 | `get_sensor_7_in_1_summary_data` | `sensor_7_in_1` | همان وضعیت |
| `sensorComparisonChart` | `implemented / transitional` | persisted sensor log | سنسور 7-in-1 | `get_sensor_7_in_1_summary_data` | `sensor_7_in_1` | همان وضعیت |
| `anomalyDetectionCard` | `implemented / transitional` | derived from sensor logs | سنسور 7-in-1 | `get_sensor_7_in_1_summary_data` | `sensor_7_in_1` | ownership نهایی anomalyها هنوز کامل یکدست نشده |
| `farmAlertsTimeline` | `partial` | persisted timeline | هشدارها | `get_alert_timeline_data` | `farm_alerts` | نباید fallback ساختگی runtime داشته باشد |
| `waterNeedPrediction` | `implemented / proxy-derived` | derived from persisted irrigation recommendation | آبیاری | `get_water_need_prediction_data` | `water` | facade در `water` است ولی business source در `irrigation` قرار دارد |
| `harvestPredictionCard` | `implemented / proxy-derived` | persisted AI-derived | برداشت/عملکرد | `get_yield_harvest_summary_data` | `yield_harvest` | از لاگ persisted می‌آید |
| `yieldPredictionChart` | `implemented / proxy-derived` | persisted AI-derived | برداشت/عملکرد | `get_yield_harvest_summary_data` | `yield_harvest` | از لاگ persisted می‌آید |
| `soilMoistureHeatmap` | `implemented / transitional` | persisted sensor log | سنسور 7-in-1 | `get_sensor_7_in_1_summary_data` | `sensor_7_in_1` | facade نهایی همه خوانش‌ها را هنوز unify نکرده |
| `ndviHealthCard` | `disabled / partial` | not runtime-ready | سلامت گیاه | `get_crop_health_summary_data` | `crop_health` | نباید به‌عنوان کارت implemented کامل معرفی شود |
| `recommendationsList` | `implemented / transitional` | aggregator | تجمیع پیشنهادها | `_build_recommendations_list` | `dashboard` | از چند app کنار هم ساخته می‌شود |
| `economicOverview` | `implemented` | persisted/log-based | نمای اقتصادی | `get_economic_overview_data` | `economic_overview` | داده اقتصادی persisted |

## نکات مهم کارت‌ها

### `farmOverviewKpis`
- aggregator است و باید در `dashboard` بماند.

### `farmWeatherCard`
- source: `water.models.WeatherForecastLog`
- قرارداد runtime: اگر داده هواشناسی موجود نباشد، باید `empty state` یا `failure contract` صریح برگردد، نه mock.

### `farmAlertsTracker`
- source: snapshot persisted
- semantics: `cached snapshot`

### `waterNeedPrediction`
- facade فعلی در `water`
- business source واقعی: `irrigation.models.IrrigationRecommendationRequest`
- semantics: `proxy-derived persisted data`

### `harvestPredictionCard` و `yieldPredictionChart`
- source: `yield_harvest.models.YieldHarvestPredictionLog`
- semantics: `persisted AI-derived`

### `ndviHealthCard`
- status: `disabled / partial`
- تا زمانی که source runtime-ready پایدار برای NDVI نهایی نشود، نباید به عنوان کارت production-ready مستند شود.

## Ownership و transitional boundaries

- plant catalog canonical در Backend شروع می‌شود.
- dashboard هنوز بعضی کارت‌ها را از facadeهای transitional می‌خواند.
- سنسور / plant / farm ownership به‌تدریج باید به facade `farm_data` نزدیک‌تر شود، ولی همه مصرف‌کننده‌ها هنوز migrate نشده‌اند.

## Response Semantics

- `farmAlertsTracker` → `cached snapshot`
- `waterNeedPrediction` → `derived from persisted irrigation recommendation`
- `harvestPredictionCard` / `yieldPredictionChart` → `persisted AI-derived snapshot`
- `farmOverviewKpis` / `recommendationsList` → `dashboard-owned aggregator`

## Known Gaps / Follow-up

- ownership نهایی خوانش سنسور بین facade `farm_data` و سرویس‌های legacy هنوز در بعضی کارت‌ها transitional است.
- `ndviHealthCard` هنوز برای runtime production-ready نیست.
