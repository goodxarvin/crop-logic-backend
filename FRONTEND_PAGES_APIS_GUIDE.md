# Frontend Pages & APIs Guide

این فایل برای تیم فرانت نوشته شده تا بدانند:

- چه app های جدیدی به بک‌اند اضافه شده‌اند
- چه API های جدیدی اضافه شده‌اند
- چه تغییراتی نسبت به commit قبلی و تغییرات فعلی انجام شده
- سیستم شبیه‌سازی گیاه چگونه به ساختار `yield_harvest` منتقل شده
- هر card داشبورد باید به کدام app و endpoint وصل شود
- هر card علاوه بر داشبورد باید در صفحه domain خودش هم نمایش داده شود

---

## خلاصه تغییرات مهم

### تغییرات مهم commit قبلی و فعلی

در تغییرات اخیر، backend از حالت monolithic dashboard mock به سمت app-based domain APIs رفته است.

یعنی به جای اینکه همه چیز فقط در `dashboard` یا فقط از AI بیاید:

- هر بخش domain اصلی app خودش را دارد
- برای چند domain جدید، API مستقل ساخته شده
- داشبورد از service های app های مختلف داده را assemble می‌کند

### مهم‌ترین تغییر معماری

سیستم `plant_simulator` دیگر app مستقل نیست و منطق آن به `yield_harvest` منتقل شده است.

این یعنی:

- فولدر `plant_simulator` حذف شده
- route های شبیه‌ساز هنوز در `api/plant-simulator/` موجودند
- اما implementation آن‌ها داخل `yield_harvest` نگهداری می‌شود

پس برای فرانت:

- صفحه Plant Simulator هنوز می‌تواند باقی بماند
- ولی از نظر backend ownership، این بخش زیرمجموعه `yield_harvest` محسوب می‌شود
- بهتر است در فرانت هم Plant Simulator به عنوان صفحه/تب وابسته به `Yield & Harvest` دیده شود

---

## app های جدید یا تغییر یافته

### 1) `crop_health`

app جدید برای:

- `ndviHealthCard`
- `farm_health_score`

هدف:

- داشتن صفحه مستقل برای سلامت محصول / NDVI
- جدا کردن health-related KPIها از `dashboard`

### 2) `WATER`

این app جایگزین ساختار قبلی `weather_forecast` شده است.

الان app `WATER` مسئول این بخش‌هاست:

- `farmWeatherCard`
- `waterNeedPrediction`
- `water_stress_index`

هدف:

- ادغام weather + water نیاز + water stress در یک domain
- ساخت صفحه مستقل برای آب و هوا و وضعیت آب

### 3) `soil`

app جدید برای:

- `avg_soil_moisture`
- `sensorRadarChart`
- `sensorComparisonChart`
- `anomalyDetectionCard`
- `soilMoistureHeatmap`

هدف:

- جدا کردن card های مرتبط با خاک و سنسور از `dashboard`
- فراهم کردن API مستقل برای صفحه Soil / Sensor Insights

### 4) `yield_harvest`

این app قبلا وجود داشت، اما نقش آن گسترده‌تر شده:

- `yieldPredictionChart`
- `harvestPredictionCard`
- `yield_prediction` KPI
- منطق `plant_simulator` هم به این app منتقل شده

### 5) `dashboard`

`dashboard` الان دیگر منبع اصلی data نیست.

وظیفه جدید آن:

- گرفتن data از service های app های مختلف
- ساخت response نهایی برای صفحه داشبورد

---

## API های جدید و فعال

## Dashboard

- `GET /api/farm-dashboard/?farm_uuid=...`
- `GET /api/farm-dashboard-config/?farm_uuid=...`
- `PATCH /api/farm-dashboard-config/`

کاربرد:

- فقط برای صفحه Dashboard اصلی
- در فرانت برای داشبورد overview از این endpoint استفاده شود

---

## Crop Health APIs

- `GET /api/crop-health/summary/`

کاربرد:

- صفحه مستقل Crop Health
- کارت‌های:
  - `farm_health_score`
  - `ndviHealthCard`

---

## WATER APIs

- `GET /api/water/card/`
- `GET /api/water/need-prediction/`
- `GET /api/water/stress-index/`
- `GET /api/water/summary/`

کاربرد:

- صفحه مستقل Water / Water & Weather
- کارت‌های:
  - `farmWeatherCard`
  - `waterNeedPrediction`
  - `water_stress_index`

نکته:

- route قدیمی `weather_forecast` دیگر برای فرانت target اصلی نیست
- فرانت باید به `api/water/...` مهاجرت کند

---

## Soil APIs

- `GET /api/soil/avg-moisture/`
- `GET /api/soil/sensor-radar-chart/`
- `GET /api/soil/sensor-comparison-chart/`
- `GET /api/soil/anomalies/`
- `GET /api/soil/moisture-heatmap/`
- `GET /api/soil/summary/`

کاربرد:

- صفحه مستقل Soil / Soil Analytics / Sensor Insights
- کارت‌های:
  - `avg_soil_moisture`
  - `sensorRadarChart`
  - `sensorComparisonChart`
  - `anomalyDetectionCard`
  - `soilMoistureHeatmap`

---

## Yield & Harvest APIs

- `GET /api/yield-harvest/summary/`

Plant Simulator routes که الان implementationشان زیر `yield_harvest` است:

- `GET /api/plant-simulator/config/`
- `GET /api/plant-simulator/state/`
- `POST /api/plant-simulator/start/`
- `POST /api/plant-simulator/stop/`
- `POST /api/plant-simulator/reset/`
- `PATCH /api/plant-simulator/environment/`

کاربرد:

- صفحه مستقل Yield & Harvest
- صفحه یا تب Plant Simulator

---

## Economic Overview APIs

- `GET /api/economic-overview/summary/`

کاربرد:

- صفحه مستقل Economic Overview
- کارت `economicOverview`

---

## Pest Detection APIs

- `GET /api/pest-detection/risk-summary/`

کاربرد:

- صفحه Pest / Disease Risk
- KPIهای:
  - `disease_risk`
  - `pest_risk`

---

## Farm Alerts APIs

در backend برای dashboard service استفاده می‌شوند:

- tracker
- timeline
- recommendations

مسیرهای موجود:

- `GET /api/farm-alerts/tracker/`
- `GET /api/farm-alerts/timeline/`
- `GET /api/farm-alerts/anomalies/`
- `GET /api/farm-alerts/recommendations/`

کاربرد:

- صفحه Alerts
- برخی recommendationها

نکته:

- در ساختار جدید، `anomalyDetectionCard` برای dashboard از `soil` می‌آید
- ولی `farm_alerts` هنوز برای timeline/tracker/recommendations مهم است

---

## تغییر سیستم Plant Simulator

### قبل

- app جداگانه‌ای به اسم `plant_simulator` وجود داشت
- config, view, route و mock data همگی در همان app بودند

### الان

- app `plant_simulator` حذف شده
- route های plant simulator حفظ شده‌اند
- implementation آن‌ها به `yield_harvest` منتقل شده

### نتیجه برای فرانت

- صفحه Plant Simulator حذف نشود
- اما در navigation و ownership بهتر است به عنوان بخشی از `Yield & Harvest` دیده شود
- اگر صفحه Yield & Harvest دارید، Plant Simulator بهتر است زیر همین domain قرار بگیرد

### پیشنهاد UI/Navigation

- `Yield & Harvest`
  - Overview
  - Yield Prediction
  - Harvest Prediction
  - Plant Simulator

---

## مپ کامل card ها به app ها

| Card | Dashboard Row | Source App | Preferred Endpoint | Frontend Page |
|---|---|---|---|---|
| `farm_health_score` | `overviewKpis` | `crop_health` | `GET /api/crop-health/summary/` | Crop Health Page |
| `water_stress_index` | `overviewKpis` | `WATER` | `GET /api/water/stress-index/` | Water Page |
| `avg_soil_moisture` | `overviewKpis` | `soil` | `GET /api/soil/avg-moisture/` | Soil Page |
| `disease_risk` | `overviewKpis` | `pest_detection` | `GET /api/pest-detection/risk-summary/` | Pest Risk Page |
| `yield_prediction` | `overviewKpis` | `yield_harvest` | `GET /api/yield-harvest/summary/` | Yield & Harvest Page |
| `pest_risk` | `overviewKpis` | `pest_detection` | `GET /api/pest-detection/risk-summary/` | Pest Risk Page |
| `farmWeatherCard` | `weatherAlerts` | `WATER` | `GET /api/water/card/` | Water Page |
| `farmAlertsTracker` | `weatherAlerts` | `farm_alerts` | `GET /api/farm-alerts/tracker/` | Alerts Page |
| `sensorValuesList` | `sensorMonitoring` | فعلا `dashboard` | فعلا فقط dashboard | Sensor Page در آینده |
| `sensorRadarChart` | `sensorCharts` | `soil` | `GET /api/soil/sensor-radar-chart/` | Soil Page |
| `sensorComparisonChart` | `sensorCharts` | `soil` | `GET /api/soil/sensor-comparison-chart/` | Soil Page |
| `anomalyDetectionCard` | `alertsWater` | `soil` | `GET /api/soil/anomalies/` | Soil Page |
| `farmAlertsTimeline` | `alertsWater` | `farm_alerts` | `GET /api/farm-alerts/timeline/` | Alerts Page |
| `waterNeedPrediction` | `alertsWater` | `WATER` | `GET /api/water/need-prediction/` | Water Page |
| `harvestPredictionCard` | `predictions` | `yield_harvest` | `GET /api/yield-harvest/summary/` | Yield & Harvest Page |
| `yieldPredictionChart` | `predictions` | `yield_harvest` | `GET /api/yield-harvest/summary/` | Yield & Harvest Page |
| `soilMoistureHeatmap` | `soilHeatmap` | `soil` | `GET /api/soil/moisture-heatmap/` | Soil Page |
| `ndviHealthCard` | `ndviRecommendations` | `crop_health` | `GET /api/crop-health/summary/` | Crop Health Page |
| `recommendationsList` | `ndviRecommendations` | ترکیبی | dashboard aggregate | Recommendations / Alerts / Domain Pages |
| `economicOverview` | `economic` | `economic_overview` | `GET /api/economic-overview/summary/` | Economic Overview Page |

---

## صفحه‌هایی که تیم فرانت باید بسازد

با توجه به backend فعلی، پیشنهاد می‌شود این صفحه‌ها حتما در فرانت ساخته شوند:

### 1) Dashboard Page

برای overview کلی مزرعه

endpoint اصلی:

- `GET /api/farm-dashboard/?farm_uuid=...`

### 2) Crop Health Page

نمایش:

- `farm_health_score`
- `ndviHealthCard`

endpoint:

- `GET /api/crop-health/summary/`

### 3) Water Page

نمایش:

- `farmWeatherCard`
- `waterNeedPrediction`
- `water_stress_index`

endpoint ها:

- `GET /api/water/card/`
- `GET /api/water/need-prediction/`
- `GET /api/water/stress-index/`
- یا یکجا `GET /api/water/summary/`

### 4) Soil Page

نمایش:

- `avg_soil_moisture`
- `sensorRadarChart`
- `sensorComparisonChart`
- `anomalyDetectionCard`
- `soilMoistureHeatmap`

endpoint ها:

- `GET /api/soil/avg-moisture/`
- `GET /api/soil/sensor-radar-chart/`
- `GET /api/soil/sensor-comparison-chart/`
- `GET /api/soil/anomalies/`
- `GET /api/soil/moisture-heatmap/`
- یا یکجا `GET /api/soil/summary/`

### 5) Yield & Harvest Page

نمایش:

- `yield_prediction`
- `yieldPredictionChart`
- `harvestPredictionCard`

endpoint:

- `GET /api/yield-harvest/summary/`

### 6) Plant Simulator Page / Tab

این صفحه باید باقی بماند، اما domain آن الان زیر `yield_harvest` است.

endpoint ها:

- `GET /api/plant-simulator/config/`
- `GET /api/plant-simulator/state/`
- `POST /api/plant-simulator/start/`
- `POST /api/plant-simulator/stop/`
- `POST /api/plant-simulator/reset/`
- `PATCH /api/plant-simulator/environment/`

### 7) Alerts Page

نمایش:

- `farmAlertsTracker`
- `farmAlertsTimeline`
- recommendationهای alert-based

endpoint ها:

- `GET /api/farm-alerts/tracker/`
- `GET /api/farm-alerts/timeline/`
- `GET /api/farm-alerts/recommendations/`

### 8) Pest / Disease Risk Page

نمایش:

- `disease_risk`
- `pest_risk`

endpoint:

- `GET /api/pest-detection/risk-summary/`

### 9) Economic Overview Page

نمایش:

- `economicOverview`

endpoint:

- `GET /api/economic-overview/summary/`

---

## قانون مهم برای تیم فرانت

هر card باید در دو جا قابل استفاده باشد:

### 1) داخل Dashboard

برای overview سریع مزرعه

### 2) داخل صفحه domain خودش

برای نمایش کامل‌تر و جزئی‌تر

یعنی:

- `ndviHealthCard` هم در Dashboard باشد هم در Crop Health Page
- `waterNeedPrediction` هم در Dashboard باشد هم در Water Page
- `soilMoistureHeatmap` هم در Dashboard باشد هم در Soil Page
- `yieldPredictionChart` هم در Dashboard باشد هم در Yield & Harvest Page
- `economicOverview` هم در Dashboard باشد هم در Economic Page

این الگو باید برای همه card های domain-based رعایت شود.

---

## پیشنهاد ساختار صفحات در فرانت

### پیشنهادی برای منوی اصلی

- Dashboard
- Crop Health
- Water
- Soil
- Yield & Harvest
- Plant Simulator
- Alerts
- Pest & Disease Risk
- Economic Overview

### پیشنهادی برای ارتباط صفحه و API

- Dashboard -> فقط dashboard aggregate
- Domain pages -> endpoint اختصاصی همان app

این روش باعث می‌شود:

- dashboard سریع‌تر و ساده‌تر بماند
- صفحات domain مستقل توسعه‌پذیر باشند
- coupling بین frontend pages و dashboard کم شود

---

## نکته مهم درباره sensorValuesList

در حال حاضر:

- `sensorValuesList` هنوز app اختصاصی ندارد
- هنوز از `dashboard/mock_data.py` می‌آید

برای فرانت:

- موقتا می‌تواند فقط در Dashboard نشان داده شود
- یا یک placeholder page برای Sensor Details ساخته شود

اما از نظر backend، این card هنوز به app اختصاصی مهاجرت نکرده است.

---

## جمع‌بندی نهایی

### app های جدید یا تغییر یافته برای فرانت

- `crop_health`
- `WATER`
- `soil`
- `yield_harvest` با نقش گسترده‌تر
- حذف `plant_simulator` به عنوان app مستقل و انتقال آن به `yield_harvest`

### چیزی که فرانت باید بداند

- dashboard دیگر منبع domain data نیست؛ فقط aggregator است
- هر card مهم الان باید app/domain خودش را داشته باشد
- هر card باید هم در dashboard باشد هم در صفحه مربوط به خودش
- Plant Simulator هنوز endpoint دارد، اما از نظر معماری بخشی از `yield_harvest` است

### بهترین rule برای تیم فرانت

اگر صفحه overview می‌خواهید:

- از `GET /api/farm-dashboard/` استفاده کنید

اگر صفحه domain می‌خواهید:

- از endpoint اختصاصی همان app استفاده کنید
