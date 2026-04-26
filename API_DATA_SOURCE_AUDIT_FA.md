# گزارش بررسی منبع داده APIها

تاریخ بررسی: 2026-04-26

## جمع‌بندی خیلی کوتاه
z
- در این repo، بیشتر endpointهایی که `external_api_request("ai", ...)` صدا می‌زنند **از mock داخلی این backend استفاده نمی‌کنند** و به‌صورت HTTP به سرویس AI می‌روند.
- دلیلش این است که در `external_api_adapter/adapter.py` شرط mock این‌طور نوشته شده: `USE_EXTERNAL_API_MOCK and service_name != "ai"`.
- در `.env` فعلی، `USE_EXTERNAL_API_MOCK=true` است، اما چون سرویس این endpointها `ai` است، باز هم درخواست‌ها به سرویس واقعیِ تنظیم‌شده در `AI_SERVICE_BASE_URL=http://ai-web:8000` می‌روند.
- پس برای endpointهای proxy شده به `ai`، از نگاه این backend، **منبع فعلی داده = سرویس واقعی AI** است، نه فایل‌های mock همین repo.
- بعضی endpointها اصلاً external call ندارند و فقط از `mock_data.py` یا از دیتابیس خود Django استفاده می‌کنند.

## مبنای تشخیص

### تنظیمات سراسری

- `USE_EXTERNAL_API_MOCK=true`
- `AI_SERVICE_BASE_URL=http://ai-web:8000`
- `AI_SERVICE_HOST_HEADER=localhost`

### رفتار adapter

در `external_api_adapter/adapter.py`:

```python
use_mock = getattr(settings, "USE_EXTERNAL_API_MOCK", False) and service_name != "ai"
```

یعنی:

- برای `farm_hub` و سرویس‌های غیر `ai` امکان mock داخلی هست.
- برای `ai` **حتی اگر** `USE_EXTERNAL_API_MOCK=true` باشد، درخواست mock نمی‌شود و مستقیم HTTP call زده می‌شود.

> نکته: این گزارش فقط نشان می‌دهد این backend داده را از کجا می‌گیرد. اینکه خود سرویس `ai-web:8000` پشت صحنه mock برگرداند یا داده واقعی تولید کند، از داخل این repo قابل اثبات نیست.

---

## 1) Pest Detection

| Endpoint | منبع داده فعلی | نوع داده فعلی | آدرس/منبع دقیق |
|---|---|---|---|
| `POST /api/pest-detection/analyze/` | سرویس AI خارجی | واقعی از دید backend | `http://ai-web:8000/api/pest-detection/analyze/` |
| `POST /api/pest-detection/risk/` | سرویس AI خارجی | واقعی از دید backend | `http://ai-web:8000/api/pest-detection/risk/` |
| `GET /api/pest-detection/risk-summary/` | سرویس AI خارجی | واقعی از دید backend | `http://ai-web:8000/api/pest-detection/risk-summary/` |

### توضیح

- هر 3 endpoint در `pest_detection/views.py` مستقیم `external_api_request("ai", ...)` صدا می‌زنند.
- فایل `pest_detection/services.py` یک mock به نام `get_risk_summary_data` دارد، ولی **در endpoint واقعی `risk-summary` استفاده نمی‌شود**.
- نتیجه: در وضعیت فعلی این 3 endpoint **mock محلی backend نیستند**.

---

## 2) Plant Simulator

| Endpoint | منبع داده فعلی | نوع داده فعلی | آدرس/منبع دقیق |
|---|---|---|---|
| `GET /api/plant-simulator/config/` | `yield_harvest.mock_data.CONFIG_SLIDERS_ONLY` | mock/static | internal |
| `PATCH /api/plant-simulator/environment/` | پاسخ ثابت success | mock/static | internal |
| `POST /api/plant-simulator/reset/` | پاسخ ثابت success | mock/static | internal |
| `POST /api/plant-simulator/start/` | `yield_harvest.mock_data.START_RESPONSE_DATA` | mock/static | internal |
| `GET /api/plant-simulator/state/` | `yield_harvest.mock_data.STATE_RESPONSE_DATA` | mock/static | internal |
| `POST /api/plant-simulator/stop/` | پاسخ ثابت success | mock/static | internal |

### توضیح

- routeهای `plant-simulator` داخل `yield_harvest/views.py` تعریف شده‌اند.
- هیچ‌کدام external API call ندارند.
- همه این endpointها فعلاً **ماک/استاتیک** هستند.

---

## 3) Soil

| Endpoint | منبع داده فعلی | نوع داده فعلی | آدرس/منبع دقیق |
|---|---|---|---|
| `GET /api/soil/anomalies/` | دیتابیس مدل `farm_alerts.AnomalyDetection` در صورت وجود farm و رکورد، وگرنه `soil.mock_data.ANOMALY_DETECTION_CARD` | ترکیبی: DB / mock | internal DB |
| `GET /api/soil/avg-moisture/` | محاسبه از `get_soil_moisture_heatmap_data()` که خودش از mock می‌آید | mock-derived | internal |
| `GET /api/soil/moisture-heatmap/` | سرویس AI خارجی | واقعی از دید backend | `http://ai-web:8000/api/soile/moisture-heatmap/` |
| `GET /api/sensor-7-in-1/sensor-comparison-chart/` | `sensor_7_in_1.services.get_sensor_comparison_chart_data` | sensor 7 in 1 | internal |
| `GET /api/sensor-7-in-1/sensor-radar-chart/` | `sensor_7_in_1.services.get_sensor_radar_chart_data` | sensor 7 in 1 | internal |
| `GET /api/soil/summary/` | سرویس AI خارجی | واقعی از دید backend | `http://ai-web:8000/api/soile/health-summary/` |

### توضیح

- `avg-moisture` داده واقعی sensor یا external API نمی‌خواند؛ فقط از heatmap ماک میانگین می‌گیرد.
- `anomalies` تنها endpoint این گروه است که **می‌تواند** از DB داخلی بخواند.
- `summary` فقط wrapper همین سرویس‌های داخلی است و خودش external call ندارد.

---

## 4) WATER

| Endpoint | منبع داده فعلی | نوع داده فعلی | آدرس/منبع دقیق |
|---|---|---|---|
| `GET /api/water/card/` | سرویس AI خارجی + ذخیره در `water.WeatherForecastLog` | واقعی از دید backend | `http://ai-web:8000/weather-forecast/card` |
| `GET /api/water/need-prediction/` | اگر `farm_uuid` معتبر باشد: سرویس AI خارجی؛ اگر نباشد: داده مشتق‌شده از `irrigation_recommendation.IrrigationRecommendationRequest` یا mock | ترکیبی | `http://ai-web:8000/api/weather/water-need-prediction/` یا internal DB/mock |
| `GET /api/water/stress-index/` | سرویس AI خارجی | واقعی از دید backend | `http://ai-web:8000/api/water/stress-index/` |
| `GET /api/water/summary/` | local aggregation از `WeatherForecastLog` + `IrrigationRecommendationRequest` + mock fallback | ترکیبی | internal DB/mock |

### توضیح

- `water/card` در لحظه درخواست از AI می‌خواند و نتیجه را در `WeatherForecastLog` ذخیره می‌کند.
- `water/need-prediction` رفتار دوحالته دارد:
  - اگر `farm_uuid` داده شود و farm پیدا شود: مستقیم به AI می‌رود.
  - اگر farm نداشته باشد: از آخرین `IrrigationRecommendationRequest` می‌سازد؛ اگر چیزی نباشد، از `water.mock_data` می‌دهد.
- `water/summary` خودش به AI زنگ نمی‌زند؛ فقط داده cached/local را assemble می‌کند.

---

## 5) WEATHER

| Endpoint | منبع داده فعلی | نوع داده فعلی | آدرس/منبع دقیق |
|---|---|---|---|
| `POST /api/weather/farm-card/` | سرویس AI خارجی + ذخیره در `WeatherForecastLog` | واقعی از دید backend | `http://ai-web:8000/weather-forecast/card` |
### توضیح

- در namespace `weather` فقط `POST /api/weather/farm-card/` باقی مانده است.
- endpoint `POST /api/weather/water-need-prediction/` حذف شده است.

---

## 6) Yield & Harvest Prediction

| Endpoint | منبع داده فعلی | نوع داده فعلی | آدرس/منبع دقیق |
|---|---|---|---|
| `GET /api/yield-harvest/summary/` | سرویس AI خارجی + ذخیره در `yield_harvest.YieldHarvestPredictionLog` | واقعی از دید backend | `http://ai-web:8000/yield-harvest/summary` |

### توضیح

- این endpoint در `yield_harvest/views.py` مستقیماً AI را صدا می‌زند.
- سپس نتیجه در `YieldHarvestPredictionLog` ذخیره می‌شود.
- سرویس `yield_harvest/services.py` برای خواندن از log و fallback mock وجود دارد، اما خود endpoint `summary` در حال حاضر **آن سرویس را استفاده نمی‌کند**.

---

## 7) Fertilization Recommendation

| Endpoint | منبع داده فعلی | نوع داده فعلی | آدرس/منبع دقیق |
|---|---|---|---|
| `GET /api/fertilization/config/` | `fertilization_recommendation.mock_data.CONFIG_RESPONSE_DATA` | mock/static | internal |
| `POST /api/fertilization/recommend/` | سرویس AI خارجی + ذخیره در `FertilizationRecommendationRequest` | واقعی از دید backend | `http://ai-web:8000/api/fertilization/recommend/` |

### توضیح

- `config` فعلاً فقط config ثابت برمی‌گرداند.
- `recommend` واقعی از نگاه backend است و پاسخ خام AI در DB ذخیره می‌شود.

---

## 8) Irrigation Recommendation

| Endpoint | منبع داده فعلی | نوع داده فعلی | آدرس/منبع دقیق |
|---|---|---|---|
| `GET /api/irrigation/` | سرویس AI خارجی | واقعی از دید backend | `http://ai-web:8000/api/irrigation/` |
| `GET /api/irrigation/config/` | `irrigation_recommendation.mock_data.CONFIG_RESPONSE_DATA` | mock/static | internal |
| `POST /api/irrigation/recommend/` | سرویس AI خارجی + ذخیره در `IrrigationRecommendationRequest` | واقعی از دید backend | `http://ai-web:8000/api/irrigation/recommend/` |

### نکته مهم درباره مسیر درخواستی شما

مسیر `POST /api/irrigation/water-stress/farm-alerts` در این backend **وجود ندارد**.

مسیرهای نزدیک و واقعی این‌ها هستند:

- `POST /api/irrigation/water-stress/`
  - منبع فعلی: سرویس AI خارجی
  - آدرس upstream: `http://ai-web:8000/api/water/stress-index/`
- endpointهای `farm-alerts` جدا هستند و زیر prefix دیگری قرار دارند:
  - `/api/farm-alerts/...`

---

## 9) Farm Alerts

| Endpoint | منبع داده فعلی | نوع داده فعلی | آدرس/منبع دقیق |
|---|---|---|---|
| `GET /api/farm-alerts/anomalies/` | `farm_alerts.mock_data.ANOMALY_DETECTION_CARD` | mock/static | internal |
| `POST /api/farm-alerts/create/` | دیتابیس داخلی (`FarmAlert`) + ساخت `FarmNotification` | internal DB | internal DB |
| `GET /api/farm-alerts/recommendations/` | `farm_alerts.mock_data.RECOMMENDATIONS_LIST` | mock/static | internal |
| `GET /api/farm-alerts/timeline/` | `farm_alerts.mock_data.FARM_ALERTS_TIMELINE` | mock/static | internal |

### نکته مهم درباره مسیر درخواستی شما

مسیر `GET /api/farm-alerts/tracker/economy` در این backend **وجود ندارد**.

مسیر درست موجود:

- `GET /api/farm-alerts/tracker/`
  - منبع فعلی: `farm_alerts.mock_data.ARM_ALERTS_TRACKER`
  - نوع: mock/static

### توضیح

- با اینکه در `farm_alerts/services.py` توابعی برای خواندن tracker/timeline/anomalies/recommendations از DB وجود دارد، viewهای فعلی از آن‌ها استفاده نمی‌کنند.
- بنابراین در وضعیت فعلی:
  - `tracker` = mock
  - `timeline` = mock
  - `anomalies` = mock
  - `recommendations` = mock
- فقط `create` واقعاً به DB داخلی می‌نویسد.

---

## 10) Economy

| Endpoint | منبع داده فعلی | نوع داده فعلی | آدرس/منبع دقیق |
|---|---|---|---|
| `POST /api/economy/overview/` | سرویس AI خارجی + ذخیره در `economic_overview.EconomicOverviewLog` | واقعی از دید backend | `http://ai-web:8000/api/economy/overview/` |

### توضیح

- endpoint تکراری `GET /api/economy/summary/` حذف شده است.
- endpoint canonical اقتصادی فقط این است:
  - `POST /api/economy/overview/`
- این endpoint داده را از AI می‌گیرد و در `EconomicOverviewLog` ذخیره می‌کند.

---

## 11) Crop Health

| Endpoint | منبع داده فعلی | نوع داده فعلی | آدرس/منبع دقیق |
|---|---|---|---|
| `POST /api/crop-health/ndvi-health/` | `crop_health.mock_data.NDVI_HEALTH_CARD` | mock/static | internal |
| `GET /api/crop-health/summary/` | `crop_health.mock_data.NDVI_HEALTH_CARD` + `crop_health.mock_data.FARM_HEALTH_SCORE` | mock/static | internal |

### توضیح

- `get_crop_health_summary_data(farm=None)` در `crop_health/services.py` پارامتر farm را نادیده می‌گیرد.
- پس حتی نسخه POST که farm را validate می‌کند هم در نهایت داده mock برمی‌گرداند.

---

## 12) Soil Data

| Endpoint | منبع داده فعلی | نوع داده فعلی | آدرس/منبع دقیق |
|---|---|---|---|
| `POST /api/soil/health/ndvi-health/` | همان `crop_health` | mock/static | internal |
| `GET /api/soil/health/summary/` | همان `crop_health` | mock/static | internal |

### توضیح

- در `config/urls.py` مسیرهای `crop_health` زیر `api/soil/health/` هم mount شده‌اند.
- یعنی این دو endpoint عملاً alias همان endpointهای `crop-health` هستند.
- بنابراین هر دو فعلاً **mock/static** هستند.

---

## 13) Crop Simulation

| Endpoint | منبع داده فعلی | نوع داده فعلی | آدرس/منبع دقیق |
|---|---|---|---|
| `POST /api/yield-harvest/crop-simulation/current-farm-chart/` | سرویس AI خارجی | واقعی از دید backend | `http://ai-web:8000/api/crop-simulation/current-farm-chart/` |
| `POST /api/yield-harvest/crop-simulation/harvest-prediction/` | سرویس AI خارجی | واقعی از دید backend | `http://ai-web:8000/api/crop-simulation/harvest-prediction/` |
| `POST /api/yield-harvest/crop-simulation/yield-prediction/` | سرویس AI خارجی | واقعی از دید backend | `http://ai-web:8000/api/crop-simulation/yield-prediction/` |

### توضیح

- هر سه endpoint در `yield_harvest/views.py` هستند.
- هر سه مستقیماً `external_api_request("ai", ...)` صدا می‌زنند.

---

## جدول نهایی وضعیت فعلی

### endpointهایی که الان از سرویس AI می‌گیرند

- `POST /api/pest-detection/analyze/`
- `POST /api/pest-detection/risk/`
- `GET /api/pest-detection/risk-summary/`
- `GET /api/water/card/`
- `GET /api/water/stress-index/`
- `POST /api/weather/farm-card/`
- `GET /api/yield-harvest/summary/`
- `POST /api/fertilization/recommend/`
- `GET /api/irrigation/`
- `POST /api/irrigation/recommend/`
- `POST /api/irrigation/water-stress/`
- `POST /api/yield-harvest/crop-simulation/current-farm-chart/`
- `POST /api/yield-harvest/crop-simulation/harvest-prediction/`
- `POST /api/yield-harvest/crop-simulation/yield-prediction/`

### endpointهایی که الان mock/static هستند

- همه `plant-simulator`
- `GET /api/soil/moisture-heatmap/`
- `GET /api/sensor-7-in-1/sensor-comparison-chart/`
- `GET /api/sensor-7-in-1/sensor-radar-chart/`
- `GET /api/fertilization/config/`
- `GET /api/irrigation/config/`
- `GET /api/farm-alerts/tracker/`
- `GET /api/farm-alerts/timeline/`
- `GET /api/farm-alerts/anomalies/`
- `GET /api/farm-alerts/recommendations/`
- `POST /api/economy/overview/`
- `POST /api/crop-health/ndvi-health/`
- `GET /api/crop-health/summary/`
- `POST /api/soil/health/ndvi-health/`
- `GET /api/soil/health/summary/`

### endpointهایی که ترکیبی هستند

- `GET /api/soil/anomalies/` → DB اگر data باشد، وگرنه mock
- `GET /api/soil/avg-moisture/` → derived from mock heatmap
- `GET /api/soil/summary/` → سرویس AI خارجی
- `GET /api/water/need-prediction/` → با `farm_uuid` معتبر معمولاً AI، بدون آن local/mock
- `GET /api/water/summary/` → local DB/cache/mock

### مسیرهایی که در این backend وجود ندارند

- `POST /api/irrigation/water-stress/farm-alerts`
- `GET /api/farm-alerts/tracker/economy`

---

## پیشنهاد برای اصلاح اگر هدف شما «داده واقعی» است

اگر بخواهید این endpointها واقعاً از داده واقعی backend خودشان بخوانند، اولویت اصلاح منطقی این‌هاست:

1. `farm_alerts/views.py`
   - به‌جای mock مستقیم، از توابع `farm_alerts/services.py` استفاده شود.
2. `economic_overview/views.py`
   - `summary` از `get_economic_overview_data()` استفاده کند، نه mock ثابت.
3. `crop_health/services.py`
   - به‌جای mock ثابت، از منبع واقعی NDVI یا cache/database استفاده کند.
4. `soil/services.py`
   - heatmap/radar/comparison از sensor logs واقعی ساخته شوند.
5. `water/summary`
   - در صورت نیاز، به‌جای cache/log فقط، امکان refresh مستقیم از AI داشته باشد.
