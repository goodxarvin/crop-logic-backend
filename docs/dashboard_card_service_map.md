# نقشه سرویس کارت های داشبورد

این فایل فقط برای پیدا کردن منبع داده هر کارت داشبورد نوشته شده است تا قبل از پیاده سازی API تجمیعی بدانیم هر کارت باید از کدام app و کدام service تغذیه شود.

## نقطه شروع فعلی

- تجمیع اصلی کارت ها الان در `dashboard/services.py` داخل تابع `get_farm_dashboard_cards` انجام می شود.
- endpoint فعلی ارسال کارت ها در `dashboard/views.py` داخل `FarmDashboardCardsView` قرار دارد.
- لیست کارت های معتبر در `dashboard/mock_data.py` داخل `VALID_CARD_IDS` نگهداری می شود.

## جمع بندی سریع

| Card ID | منبع اصلی | تابع/سرویس فعلی | app داده | توضیح |
| --- | --- | --- | --- | --- |
| `farmOverviewKpis` | تجمیع چند سرویس | `_build_overview_kpis` | `dashboard` | خودش داده مستقل ندارد و از چند app ساخته می شود |
| `farmWeatherCard` | آب و هوا | `get_farm_weather_card_data` | `water` | از لاگ پیش بینی هوا می آید |
| `farmAlertsTracker` | هشدارها | `get_alert_tracker_data` | `farm_alerts` | شمارش هشدارهای فعال |
| `sensorValuesList` | سنسور 7-in-1 | `get_sensor_7_in_1_summary_data` | `sensor_7_in_1` | لیست آخرین مقادیر سنسور |
| `sensorRadarChart` | سنسور 7-in-1 | `get_sensor_7_in_1_summary_data` | `sensor_7_in_1` | امتیازدهی راداری وضعیت سنسور |
| `sensorComparisonChart` | سنسور 7-in-1 | `get_sensor_7_in_1_summary_data` | `sensor_7_in_1` | مقایسه تاریخی رطوبت خاک |
| `anomalyDetectionCard` | سنسور 7-in-1 | `get_sensor_7_in_1_summary_data` | `sensor_7_in_1` | ناهنجاری های خارج از بازه مجاز |
| `farmAlertsTimeline` | هشدارها | `get_alert_timeline_data` | `farm_alerts` | تایم لاین هشدارها |
| `waterNeedPrediction` | آبیاری | `get_water_need_prediction_data` | `water` | عملا از نتیجه آبیاری می خواند |
| `harvestPredictionCard` | برداشت/عملکرد | `get_yield_harvest_summary_data` | `yield_harvest` | زمان برداشت و بازه بهینه |
| `yieldPredictionChart` | برداشت/عملکرد | `get_yield_harvest_summary_data` | `yield_harvest` | نمودار پیش بینی عملکرد |
| `soilMoistureHeatmap` | سنسور 7-in-1 | `get_sensor_7_in_1_summary_data` | `sensor_7_in_1` | هیت مپ رطوبت خاک |
| `ndviHealthCard` | سلامت گیاه | `get_crop_health_summary_data` | `crop_health` | فعلا mock است |
| `recommendationsList` | تجمیع پیشنهادها | `_build_recommendations_list` | `dashboard` | از چند app کنار هم ساخته می شود |
| `economicOverview` | نمای اقتصادی | `get_economic_overview_data` | `economic_overview` | داده اقتصادی و سری نمودار |

## جزئیات هر کارت

### 1) `farmOverviewKpis`

این کارت در `dashboard/services.py` و توسط `_build_overview_kpis` ساخته می شود و داده اش از چند app می آید:

- `crop_health.services.get_crop_health_summary_data`
  - KPI: `farmHealthScore`
- `water.services.get_water_stress_index_data`
  - KPI: `water_stress_index`
- `sensor_7_in_1.services.get_sensor_7_in_1_summary_data`
  - KPI: `avgSoilMoisture`
- `pest_detection.services.get_risk_summary_data`
  - KPI ها: `disease_risk` و `pest_risk`
- `yield_harvest.services.get_yield_harvest_summary_data`
  - KPI: `yield_prediction_card`

نتیجه: این بخش باید در API نهایی به صورت aggregator باقی بماند، چون منبع واحد ندارد.

### 2) `farmWeatherCard`

- app: `water`
- service: `water/services.py` -> `get_farm_weather_card_data`
- model/source: `water.models.WeatherForecastLog`
- fallback: `water/mock_data.py` -> `FARM_WEATHER_CARD`

اگر داده هواشناسی برای مزرعه ثبت نشده باشد، خروجی mock برمی گردد.

### 3) `farmAlertsTracker`

- app: `farm_alerts`
- service: `farm_alerts/services.py` -> `get_alert_tracker_data`
- model/source: `farm_alerts.models.FarmAlert`
- منطق: هشدارهای `is_active=True` را می شمارد و top 3 را برمی گرداند.

### 4) `sensorValuesList`

- app: `sensor_7_in_1`
- service: `sensor_7_in_1/services.py` -> `get_sensor_7_in_1_summary_data`
- زیرسرویس واقعی: `get_sensor_7_in_1_values_list_data`
- source dependency:
  - `farm.sensors`
  - `sensor_external_api.services.get_sensor_external_request_logs_for_farm`
  - `sensor_external_api.services.get_farm_sensor_map_for_logs`

این کارت وابسته به آخرین لاگ سنسور فیزیکی مزرعه است.

### 5) `sensorRadarChart`

- app: `sensor_7_in_1`
- service: `sensor_7_in_1/services.py` -> `get_sensor_7_in_1_summary_data`
- زیرسرویس واقعی: `get_sensor_7_in_1_radar_chart_data`
- source: همان context سنسور 7-in-1

### 6) `sensorComparisonChart`

- app: `sensor_7_in_1`
- service: `sensor_7_in_1/services.py` -> `get_sensor_7_in_1_summary_data`
- زیرسرویس واقعی: `get_sensor_7_in_1_comparison_chart_data`
- source: history لاگ های سنسور در `sensor_external_api`

### 7) `anomalyDetectionCard`

- app: `sensor_7_in_1`
- service: `sensor_7_in_1/services.py` -> `get_sensor_7_in_1_summary_data`
- زیرسرویس واقعی: `get_sensor_7_in_1_anomaly_detection_card_data`
- منطق: از روی بازه مجاز هر فیلد سنسور anomaly می سازد.

نکته: در `farm_alerts` هم تابع `get_anomaly_detection_data` وجود دارد، ولی در داشبورد فعلی استفاده نشده و کارت anomaly از `sensor_7_in_1` می آید.

### 8) `farmAlertsTimeline`

- app: `farm_alerts`
- service: `farm_alerts/services.py` -> `get_alert_timeline_data`
- model/source: `farm_alerts.models.FarmAlert`
- fallback: `farm_alerts/mock_data.py` -> `FARM_ALERTS_TIMELINE`

### 9) `waterNeedPrediction`

- app aggregator call: `water`
- service: `water/services.py` -> `get_water_need_prediction_data`
- source واقعی داده: `irrigation.models.IrrigationRecommendationRequest`
- منطق: از `response_payload` آخرین recommendation آبیاری، `water_balance.daily` را می خواند.

نکته مهم: تابعی با همین نام در `irrigation/services.py` هم وجود دارد، اما داشبورد فعلی نسخه `water` را صدا می زند. پس منبع business data عملا app آبیاری است، ولی facade فعلی داخل app `water` قرار دارد.

### 10) `harvestPredictionCard`

- app: `yield_harvest`
- service: `yield_harvest/services.py` -> `get_yield_harvest_summary_data`
- model/source: `yield_harvest.models.YieldHarvestPredictionLog`
- داده های مهم: `harvest_date`, `days_until_harvest`, `optimal_window_start`, `optimal_window_end`

### 11) `yieldPredictionChart`

- app: `yield_harvest`
- service: `yield_harvest/services.py` -> `get_yield_harvest_summary_data`
- model/source: `yield_harvest.models.YieldHarvestPredictionLog`
- داده مهم: `chart_data`

### 12) `soilMoistureHeatmap`

- app: `sensor_7_in_1`
- service: `sensor_7_in_1/services.py` -> `get_sensor_7_in_1_summary_data`
- زیرسرویس واقعی: `get_sensor_7_in_1_soil_moisture_heatmap_data`
- source: history رطوبت خاک از لاگ سنسورها

### 13) `ndviHealthCard`

- app: `crop_health`
- service: `crop_health/services.py` -> `get_crop_health_summary_data`
- وضعیت فعلی: فعلا مستقیم از mock برمی گردد.
- fallback/source: `crop_health/mock_data.py`

نکته: این app الان منبع DB-driven در این سرویس ندارد و اگر بخواهیم داده واقعی بدهیم باید مدل یا integration منبع NDVI را همینجا اضافه کنیم.

### 14) `recommendationsList`

این کارت در `dashboard/services.py` و توسط `_build_recommendations_list` ساخته می شود. منابع آن:

- `farm_alerts.services.get_recommendations_list_data`
  - model/source: `farm_alerts.models.Recommendation`
- `irrigation.services.get_irrigation_dashboard_recommendation`
  - model/source: `irrigation.models.IrrigationRecommendationRequest`
- `fertilization.services.get_fertilization_dashboard_recommendation`
  - model/source: `fertilization.models.FertilizationRecommendationRequest`
- `yield_harvest.services.get_yield_harvest_summary_data`
  - برای ساخت recommendation مرتبط با بازه برداشت

نتیجه: این کارت هم aggregator است و بهتر است داخل app `dashboard` بماند.

### 15) `economicOverview`

- app: `economic_overview`
- service: `economic_overview/services.py` -> `get_economic_overview_data`
- model/source: `economic_overview.models.EconomicOverviewLog`
- فیلدهای مهم: `economic_data`, `chart_series`, `chart_categories`

## سرویس هایی که الان ماهیت aggregator دارند

این بخش ها باید در API نهایی dashboard به صورت orchestration بین app ها مدیریت شوند:

- `farmOverviewKpis`
- `recommendationsList`
- کل تابع `get_farm_dashboard_cards`

## app هایی که الان بیشتر mock هستند

این app ها در مسیر داشبورد فعلی هنوز کاملا به داده واقعی وصل نشده اند یا بخشی از خروجی آن ها mock است:

- `crop_health`
- `pest_detection`
- بعضی fallback های `water`, `farm_alerts`, `yield_harvest`, `sensor_7_in_1`

## پیشنهاد برای مرحله بعد

برای ساخت API تجمیعی تمیز، بهتر است این قرارداد را نگه داریم:

1. هر app فقط یک service کوچک برای data payload کارت خودش بدهد.
2. app `dashboard` فقط orchestration و merge انجام دهد.
3. برای کارت های ترکیبی مثل `farmOverviewKpis` و `recommendationsList` منطق join داخل `dashboard/services.py` بماند.
4. اگر خواستی endpoint جدید بسازی، `dashboard/views.py` بهترین محل برای API نهایی است چون همین حالا هم farm validation و access control آنجا انجام می شود.
