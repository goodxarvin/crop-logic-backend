# بررسی اتصال routeهای درخواستی به سرویس AI

این گزارش فقط بر اساس کد backend تهیه شده و معیار آن این است:

- آیا در کد، `external_api_request(...)` یا `external_request(...)` با **همین route** به سرویس `ai` زده می‌شود یا نه
- اگر با route دیگری به AI متصل شده باشد، route واقعی ذکر شده
- اگر اصلا اتصال AI برای آن route پیدا نشود، به عنوان `متصل نیست` علامت خورده

## متصل به AI با همین route

| API | اتصال | شواهد |
|---|---|---|
| `POST /api/rag/chat/` | بله | `farm_ai_assistant/views.py:511` |
| `POST /api/soile/moisture-heatmap/` | بله | `soil/views.py:136` |
| `POST /api/soile/health-summary/` | بله | `soil/views.py:182` |
| `POST /api/soile/anomaly-detection/` | بله | `soil/views.py:90` |
| `POST /api/farm-data/` | بله | `farm_hub/services.py:166`, `farm_hub/services.py:89`, `sensor_external_api/services.py:165`, `sensor_external_api/services.py:125` |
| `POST /api/weather/water-need-prediction/` | بله | `water/views.py:136` |
| `POST /api/economy/overview/` | بله | `economic_overview/views.py:73` |
| `GET /api/irrigation/` | بله | `irrigation_recommendation/views.py:78` |
| `POST /api/irrigation/recommend/` | بله | `irrigation_recommendation/views.py:165` |
| `POST /api/fertilization/recommend/` | بله | `fertilization_recommendation/views.py:122` |
| `POST /api/crop-simulation/growth/` | بله | `yield_harvest/views.py:247` |
| `GET /api/crop-simulation/growth/<task_id>/status/` | بله | `yield_harvest/views.py:293` |
| `POST /api/crop-simulation/current-farm-chart/` | بله | `yield_harvest/views.py:145`, `yield_harvest/views.py:162` |
| `POST /api/crop-simulation/harvest-prediction/` | بله | `yield_harvest/views.py:174`, `yield_harvest/views.py:191` |
| `POST /api/crop-simulation/yield-prediction/` | بله | `yield_harvest/views.py:203`, `yield_harvest/views.py:220` |

## به AI وصل هستند، اما نه با همین route

| API درخواستی | وضعیت | route واقعی AI در کد | شواهد |
|---|---|---|---|
| `POST /api/weather/farm-card/` | با همین route به AI وصل نیست | `GET /weather-forecast/card` | `water/views.py:49` |
| `POST /api/irrigation/water-stress/` | با همین route به AI وصل نیست | `GET /api/water/stress-index/` | `irrigation_recommendation/views.py:246` |
| `POST /api/pest-disease/detect/` | با همین route به AI وصل نیست | `POST /api/pest-detection/analyze/` | `pest_detection/views.py:161` |
| `POST /api/pest-disease/risk/` | با همین route به AI وصل نیست | `POST /api/pest-detection/risk/` | `pest_detection/views.py:202` |
| `POST /api/pest-disease/risk-summary/` | با همین route به AI وصل نیست | `GET /api/pest-detection/risk-summary/` | `pest_detection/views.py:235` |
| `POST /api/soil-data/ndvi-health/` | با همین route به AI وصل نیست | برای این path اتصال AI پیدا نشد؛ endpoint محلی پروژه با path دیگری ارائه شده | `crop_health/urls.py:6`, `crop_health/tests.py:82` |
| `POST /api/irrigation/` | route به AI با همین method پیدا نشد | فقط `GET /api/irrigation/` در کد استفاده می‌شود | `irrigation_recommendation/views.py:78` |

## متصل نیستند

برای این routeها هیچ اتصال معناداری به سرویس AI با همین path در کد پیدا نشد.

| API | وضعیت | توضیح |
|---|---|---|
| `POST /api/farm-alerts/tracker/` | متصل نیست | view محلی mock دارد و اصلا به AI call نمی‌زند |
| `POST /api/farm-alerts/timeline/` | متصل نیست | view محلی mock دارد و اصلا به AI call نمی‌زند |
| `GET /api/soil-data/` | متصل نیست | فقط spec/mock در `external_api_adapter/json/ai/index.json` دیده شد |
| `POST /api/soil-data/` | عملا با همین route متصل نیست | در `crop_zoning/services.py` call به `/soil-data` بدون پیشوند `/api` وجود دارد |
| `GET /api/soil-data/tasks/<task_id>/status/` | متصل نیست | فقط spec/mock در `external_api_adapter/json/ai/index.json` دیده شد |
| `GET /api/farm-data/<farm_uuid>/detail/` | متصل نیست | هیچ call یا route معناداری پیدا نشد |
| `POST /api/farm-data/parameters/` | متصل نیست | هیچ call یا route معناداری پیدا نشد |
| `GET /api/plants/` | متصل نیست | فقط spec/mock در `external_api_adapter/json/ai/index.json` دیده شد |
| `POST /api/plants/` | متصل نیست | فقط spec/mock در `external_api_adapter/json/ai/index.json` دیده شد |
| `GET /api/plants/<pk>/` | متصل نیست | فقط spec/mock در `external_api_adapter/json/ai/index.json` دیده شد |
| `PUT /api/plants/<pk>/` | متصل نیست | فقط spec/mock در `external_api_adapter/json/ai/index.json` دیده شد |
| `PATCH /api/plants/<pk>/` | متصل نیست | فقط spec/mock در `external_api_adapter/json/ai/index.json` دیده شد |
| `DELETE /api/plants/<pk>/` | متصل نیست | فقط spec/mock در `external_api_adapter/json/ai/index.json` دیده شد |
| `POST /api/plants/fetch-info/` | متصل نیست | فقط spec/mock در `external_api_adapter/json/ai/index.json` دیده شد |
| `GET /api/irrigation/<pk>/` | متصل نیست | route detail/call به AI پیدا نشد |
| `PUT /api/irrigation/<pk>/` | متصل نیست | route detail/call به AI پیدا نشد |
| `PATCH /api/irrigation/<pk>/` | متصل نیست | route detail/call به AI پیدا نشد |
| `DELETE /api/irrigation/<pk>/` | متصل نیست | route detail/call به AI پیدا نشد |

## نکات مهم

- `crop-simulation` ها هنوز در `yield_harvest/views.py` به AI وصل هستند، ولی route عمومی backend آن‌ها حذف شده است.
- `farm-alerts/tracker` و `farm-alerts/timeline` در backend وجود دارند، اما داده‌شان mock است و به AI وصل نیستند.
- `weather/farm-card` برای AI از route دیگری استفاده می‌کند: `/weather-forecast/card`.
- `irrigation/water-stress` هم به جای route درخواستی، به `/api/water/stress-index/` روی AI وصل شده است.
- `soil-data` وضعیت یکدستی ندارد: specهای mock برای `/api/soil-data/...` موجود است، ولی call واقعی کد به `/soil-data` بدون پیشوند `/api` دیده می‌شود.

## جمع‌بندی

- متصل به AI با همین route: `15` مورد
- متصل به AI ولی با route متفاوت: `7` مورد
- متصل نیست: `18` مورد
