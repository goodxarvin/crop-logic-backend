# Dashboard Card Sources

این فایل مشخص می‌کند هر کارت داشبورد در بک‌اند از کدام app، service و endpoint تغذیه می‌شود.

## مسیر اصلی داشبورد

- `GET /api/farm-dashboard/?farm_uuid=...`
- تجمیع نهایی کارت‌ها در `dashboard/services.py` انجام می‌شود.
- این سرویس از app های مختلف داده را جمع می‌کند و response نهایی داشبورد را می‌سازد.

## مپ ردیف‌ها و کارت‌ها

### `overviewKpis`

این ردیف در نهایت در `dashboard/services.py` ساخته می‌شود، ولی هر KPI از app خودش می‌آید:

| Card / KPI ID | عنوان | منبع اصلی | service | endpoint |
|---|---|---|---|---|
| `farm_health_score` | امتیاز سلامت مزرعه | `crop_health` | `get_crop_health_summary_data` | `GET /api/crop-health/summary/` |
| `water_stress_index` | شاخص تنش آبی | `WATER` | `get_water_stress_index_data` | `GET /api/water/stress-index/` |
| `avg_soil_moisture` | میانگین رطوبت خاک | `soil` | `get_avg_soil_moisture_data` | `GET /api/soil/avg-moisture/` |
| `disease_risk` | ریسک بیماری | `pest_detection` | `get_risk_summary_data` | `GET /api/pest-detection/risk-summary/` |
| `yield_prediction` | پیش‌بینی عملکرد | `yield_harvest` | `get_yield_harvest_summary_data` | `GET /api/yield-harvest/summary/` |
| `pest_risk` | ریسک آفات | `pest_detection` | `get_risk_summary_data` | `GET /api/pest-detection/risk-summary/` |

### `weatherAlerts`

| Card ID | عنوان | منبع اصلی | service | endpoint |
|---|---|---|---|---|
| `farmWeatherCard` | کارت آب‌وهوا | `WATER` | `get_farm_weather_card_data` | `GET /api/water/card/` |
| `farmAlertsTracker` | خلاصه هشدارها | `farm_alerts` | `get_alert_tracker_data` | هنوز endpoint مستقل service-based ندارد؛ در داشبورد از service داخلی استفاده می‌شود |

### `sensorMonitoring`

| Card ID | عنوان | منبع اصلی | service | endpoint |
|---|---|---|---|---|
| `sensorValuesList` | لیست مقادیر سنسورها | فعلا `dashboard` | فعلا مستقیم از `dashboard/mock_data.py` | endpoint مستقل ندارد |

### `sensorCharts`

| Card ID | عنوان | منبع اصلی | service | endpoint |
|---|---|---|---|---|
| `sensorRadarChart` | نمودار راداری سنسورها | `soil` | `get_sensor_radar_chart_data` | `GET /api/soil/sensor-radar-chart/` |
| `sensorComparisonChart` | مقایسه با هفته قبل | `soil` | `get_sensor_comparison_chart_data` | `GET /api/soil/sensor-comparison-chart/` |

### `alertsWater`

| Card ID | عنوان | منبع اصلی | service | endpoint |
|---|---|---|---|---|
| `anomalyDetectionCard` | ناهنجاری سنسورها/خاک | `soil` | `get_anomaly_detection_card_data` | `GET /api/soil/anomalies/` |
| `farmAlertsTimeline` | تایم‌لاین هشدارها | `farm_alerts` | `get_alert_timeline_data` | هنوز endpoint مستقل service-based ندارد؛ در داشبورد از service داخلی استفاده می‌شود |
| `waterNeedPrediction` | نیاز آبی 7 روز آینده | `WATER` | `get_water_need_prediction_data` | `GET /api/water/need-prediction/` |

### `predictions`

| Card ID | عنوان | منبع اصلی | service | endpoint |
|---|---|---|---|---|
| `harvestPredictionCard` | پیش‌بینی برداشت | `yield_harvest` | `get_yield_harvest_summary_data` | `GET /api/yield-harvest/summary/` |
| `yieldPredictionChart` | نمودار پیش‌بینی عملکرد | `yield_harvest` | `get_yield_harvest_summary_data` | `GET /api/yield-harvest/summary/` |

### `soilHeatmap`

| Card ID | عنوان | منبع اصلی | service | endpoint |
|---|---|---|---|---|
| `soilMoistureHeatmap` | نقشه حرارتی رطوبت خاک | `soil` | `get_soil_moisture_heatmap_data` | `GET /api/soil/moisture-heatmap/` |

### `ndviRecommendations`

| Card ID | عنوان | منبع اصلی | service | endpoint |
|---|---|---|---|---|
| `ndviHealthCard` | کارت سلامت NDVI | `crop_health` | `get_crop_health_summary_data` | `GET /api/crop-health/summary/` |
| `recommendationsList` | لیست پیشنهادها | ترکیبی | ترکیب در `dashboard/services.py` | endpoint مستقل نهایی ندارد |

منابع `recommendationsList`:

- `farm_alerts` از `get_recommendations_list_data`
- `irrigation_recommendation` از `get_irrigation_dashboard_recommendation`
- `fertilization_recommendation` از `get_fertilization_dashboard_recommendation`
- `yield_harvest` برای آیتم بازه برداشت

### `economic`

| Card ID | عنوان | منبع اصلی | service | endpoint |
|---|---|---|---|---|
| `economicOverview` | نمای اقتصادی | `economic_overview` | `get_economic_overview_data` | `GET /api/economic-overview/summary/` |

## endpoint های summary جدید برای app ها

برای استفاده راحت‌تر در فرانت، این app ها الان منبع واضح برای کارت‌های داشبورد دارند:

- `crop_health`
  - `GET /api/crop-health/summary/`
- `WATER`
  - `GET /api/water/card/`
  - `GET /api/water/need-prediction/`
  - `GET /api/water/stress-index/`
  - `GET /api/water/summary/`
- `soil`
  - `GET /api/soil/avg-moisture/`
  - `GET /api/soil/sensor-radar-chart/`
  - `GET /api/soil/sensor-comparison-chart/`
  - `GET /api/soil/anomalies/`
  - `GET /api/soil/moisture-heatmap/`
  - `GET /api/soil/summary/`
- `yield_harvest`
  - `GET /api/yield-harvest/summary/`
- `economic_overview`
  - `GET /api/economic-overview/summary/`

## وضعیت فعلی کارت‌ها

### کاملا service-based

- `farmOverviewKpis` به صورت ترکیبی
- `farmWeatherCard`
- `farmAlertsTracker`
- `sensorRadarChart`
- `sensorComparisonChart`
- `anomalyDetectionCard`
- `farmAlertsTimeline`
- `waterNeedPrediction`
- `harvestPredictionCard`
- `yieldPredictionChart`
- `soilMoistureHeatmap`
- `ndviHealthCard`
- `recommendationsList`
- `economicOverview`

### هنوز مستقیم از mock داشبورد

- `sensorValuesList`

## پیشنهاد برای فرانت

- اگر صفحه مستقل برای هر domain دارید، برای هر صفحه از endpoint خود همان app استفاده کنید.
- اگر صفحه داشبورد اصلی دارید، فقط از `GET /api/farm-dashboard/?farm_uuid=...` استفاده کنید.
- اگر لازم است هر کارت به صفحه جزئیات خودش لینک شود، بهترین mapping فعلی این است:
  - Weather + Water cards -> `WATER`
  - NDVI + Farm Health -> `crop_health`
  - Soil cards -> `soil`
  - Yield + Harvest -> `yield_harvest`
  - Alerts -> `farm_alerts`
  - Economy -> `economic_overview`
  - Pest/Disease risk -> `pest_detection`
