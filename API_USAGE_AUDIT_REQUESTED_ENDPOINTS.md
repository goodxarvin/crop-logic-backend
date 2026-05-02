# گزارش وضعیت استفاده APIهای درخواستی

این گزارش فقط بر اساس کد همین repository تهیه شده است و برای هر API سه چیز بررسی شده:

- آیا به عنوان route واقعی در Django backend اکسپوز شده است یا نه
- آیا در کد، تست‌ها، داکیومنت‌های پروژه یا adapterها به آن ارجاع داده شده است یا نه
- اگر path/method اشتباه باشد، نزدیک‌ترین endpoint واقعی پروژه چیست

## 1) استفاده‌شده و فعال در backend

این APIها هم در routeهای backend وجود دارند و هم در کد/تست/داک پروژه استفاده شده‌اند.

| API | وضعیت | شواهد |
|---|---|---|
| `POST /api/weather/farm-card/` | فعال و استفاده‌شده | `water/weather_urls.py`, `water/views.py`, `water/tests.py` |
| `POST /api/economy/overview/` | فعال و استفاده‌شده | `economic_overview/urls.py`, `economic_overview/views.py`, `FRONTEND_PAGES_APIS_GUIDE.md` |
| `GET /api/irrigation/` | فعال و استفاده‌شده | `irrigation/urls.py`, `irrigation/views.py`, `API_DATA_SOURCE_AUDIT_FA.md` |
| `POST /api/irrigation/recommend/` | فعال و استفاده‌شده | `irrigation/urls.py`, `irrigation/views.py`, `irrigation/tests.py` |
| `POST /api/irrigation/water-stress/` | فعال و استفاده‌شده | `irrigation/urls.py`, `irrigation/tests.py` |
| `POST /api/fertilization/recommend/` | فعال و استفاده‌شده | `fertilization/urls.py`, `fertilization/views.py`, `API_DATA_SOURCE_AUDIT_FA.md` |

## 2) در پروژه استفاده شده‌اند، اما به عنوان endpoint مستقیم backend اکسپوز نیستند

این‌ها یا فقط به عنوان path سرویس خارجی AI استفاده می‌شوند، یا route داخلی‌شان با path دیگری در backend ارائه شده است.

| API | وضعیت | توضیح | شواهد |
|---|---|---|---|
| `POST /api/rag/chat/` | استفاده داخلی | route محلی نیست؛ به عنوان درخواست خروجی به سرویس AI استفاده می‌شود | `farm_ai_assistant/views.py`, `external_api_adapter/json/ai/index.json` |
| `GET /api/soil-data/` | فقط contract/mock | route محلی ندارد؛ فقط در adapter mock/spec آمده | `external_api_adapter/json/ai/index.json` |
| `POST /api/soil-data/` | استفاده داخلی/contract | route محلی ندارد؛ mock/spec دارد و integration نزدیک آن در `crop_zoning` به `/soil-data` صدا زده می‌شود | `external_api_adapter/json/ai/index.json`, `crop_zoning/services.py` |
| `GET /api/soil-data/tasks/<task_id>/status/` | فقط contract/mock | route محلی ندارد؛ فقط در adapter mock/spec آمده | `external_api_adapter/json/ai/index.json` |
| `POST /api/soile/moisture-heatmap/` | استفاده داخلی | backend به جای آن `POST /api/soil/moisture-heatmap/` را اکسپوز کرده و این path را به AI صدا می‌زند | `soil/views.py`, `soil/tests.py`, `soil/urls.py` |
| `POST /api/soile/health-summary/` | استفاده داخلی | backend به جای آن `POST /api/soil/summary/` را اکسپوز کرده و این path را به AI صدا می‌زند | `soil/views.py`, `soil/tests.py`, `soil/urls.py` |
| `POST /api/soile/anomaly-detection/` | استفاده داخلی | backend به جای آن `POST /api/soil/anomalies/` را اکسپوز کرده و این path را به AI صدا می‌زند | `soil/views.py`, `soil/tests.py`, `soil/urls.py` |
| `POST /api/farm-data/` | استفاده داخلی | route محلی ندارد؛ برای sync داده مزرعه به سرویس بیرونی استفاده می‌شود | `farm_hub/services.py`, `sensor_external_api/services.py`, `farm_hub/tests.py` |
| `POST /api/weather/water-need-prediction/` | استفاده داخلی | route محلی ندارد؛ backend endpoint معادل را با `GET /api/water/need-prediction/` ارائه می‌کند و خودش این path را به AI صدا می‌زند | `water/views.py`, `water/urls.py`, `water/tests.py` |
| `POST /api/crop-simulation/growth/` | استفاده باقیمانده در کد | route آن حذف شده، ولی هنوز در view/testها ارجاع مانده | `yield_harvest/views.py`, `yield_harvest/tests.py` |
| `GET /api/crop-simulation/growth/<task_id>/status/` | استفاده باقیمانده در کد | route آن حذف شده، ولی هنوز در view/testها ارجاع مانده | `yield_harvest/views.py`, `yield_harvest/tests.py` |
| `POST /api/crop-simulation/current-farm-chart/` | استفاده باقیمانده در کد | route آن حذف شده، ولی هنوز به عنوان AI path در کد وجود دارد | `yield_harvest/views.py`, `yield_harvest/tests.py` |
| `POST /api/crop-simulation/harvest-prediction/` | استفاده باقیمانده در کد | route آن حذف شده، ولی هنوز به عنوان AI path در کد وجود دارد | `yield_harvest/views.py`, `yield_harvest/tests.py` |
| `POST /api/crop-simulation/yield-prediction/` | استفاده باقیمانده در کد | route آن حذف شده، ولی هنوز به عنوان AI path در کد وجود دارد | `yield_harvest/views.py` |

## 3) در لیست شما آمده‌اند، اما با method/path فعلی استفاده نمی‌شوند

این‌ها یا method اشتباه دارند، یا path صحیح پروژه چیز دیگری است، یا اصلا implementation محلی برایشان پیدا نشد.

| API | وضعیت | توضیح | شواهد |
|---|---|---|---|
| `POST /api/farm-alerts/tracker/` | استفاده نمی‌شود | path وجود دارد ولی فقط `GET` پیاده‌سازی شده | `farm_alerts/urls.py`, `farm_alerts/views.py`, `FRONTEND_PAGES_APIS_GUIDE.md` |
| `POST /api/farm-alerts/timeline/` | استفاده نمی‌شود | path وجود دارد ولی فقط `GET` پیاده‌سازی شده | `farm_alerts/urls.py`, `farm_alerts/views.py`, `FRONTEND_PAGES_APIS_GUIDE.md` |
| `POST /api/soil-data/ndvi-health/` | استفاده نمی‌شود | endpoint واقعی پروژه `POST /api/soil/health/ndvi-health/` است | `crop_health/tests.py`, `crop_health/urls.py` |
| `GET /api/farm-data/<farm_uuid>/detail/` | استفاده نمی‌شود | route یا reference معناداری پیدا نشد | جستجو در کل repo |
| `POST /api/farm-data/parameters/` | استفاده نمی‌شود | route یا reference معناداری پیدا نشد | جستجو در کل repo |
| `GET /api/plants/` | استفاده نمی‌شود | فقط در mock/spec های adapter دیده شد؛ route محلی ندارد | `external_api_adapter/json/ai/index.json` |
| `POST /api/plants/` | استفاده نمی‌شود | فقط در mock/spec های adapter دیده شد؛ route محلی ندارد | `external_api_adapter/json/ai/index.json` |
| `GET /api/plants/<pk>/` | استفاده نمی‌شود | فقط در mock/spec های adapter دیده شد؛ route محلی ندارد | `external_api_adapter/json/ai/index.json` |
| `PUT /api/plants/<pk>/` | استفاده نمی‌شود | فقط در mock/spec های adapter دیده شد؛ route محلی ندارد | `external_api_adapter/json/ai/index.json` |
| `PATCH /api/plants/<pk>/` | استفاده نمی‌شود | فقط در mock/spec های adapter دیده شد؛ route محلی ندارد | `external_api_adapter/json/ai/index.json` |
| `DELETE /api/plants/<pk>/` | استفاده نمی‌شود | فقط در mock/spec های adapter دیده شد؛ route محلی ندارد | `external_api_adapter/json/ai/index.json` |
| `POST /api/plants/fetch-info/` | استفاده نمی‌شود | فقط در mock/spec های adapter دیده شد؛ route محلی ندارد | `external_api_adapter/json/ai/index.json` |
| `POST /api/pest-disease/detect/` | استفاده نمی‌شود | endpoint واقعی پروژه `POST /api/pest-detection/analyze/` است | `pest_detection/urls.py`, `pest_detection/views.py` |
| `POST /api/pest-disease/risk/` | استفاده نمی‌شود | endpoint واقعی پروژه `POST /api/pest-detection/risk/` است | `pest_detection/urls.py`, `pest_detection/views.py` |
| `POST /api/pest-disease/risk-summary/` | استفاده نمی‌شود | path و method هر دو متفاوت‌اند؛ endpoint واقعی `GET /api/pest-detection/risk-summary/` است | `pest_detection/urls.py`, `pest_detection/views.py`, `pest_detection/tests.py` |
| `POST /api/irrigation/` | استفاده نمی‌شود | path وجود دارد ولی فقط `GET` list پیاده‌سازی شده | `irrigation/urls.py`, `irrigation/views.py` |
| `GET /api/irrigation/<pk>/` | استفاده نمی‌شود | route detail پیدا نشد | `irrigation/urls.py` |
| `PUT /api/irrigation/<pk>/` | استفاده نمی‌شود | route detail/update پیدا نشد | `irrigation/urls.py` |
| `PATCH /api/irrigation/<pk>/` | استفاده نمی‌شود | route detail/update پیدا نشد | `irrigation/urls.py` |
| `DELETE /api/irrigation/<pk>/` | استفاده نمی‌شود | route detail/delete پیدا نشد | `irrigation/urls.py` |

## 4) جمع‌بندی سریع

- فعال و قابل استفاده در backend: `6` مورد
- استفاده داخلی یا باقیمانده در کد ولی بدون route مستقیم: `14` مورد
- استفاده‌نشده / path یا method اشتباه / بدون implementation: `20` مورد

## 5) نکات مهم برای پاک‌سازی

- `crop-simulation` routeها حذف شده‌اند، ولی referenceهای آن هنوز در `yield_harvest/views.py` و `yield_harvest/tests.py` باقی مانده‌اند.
- `rag/chat` و `farm-data` بیشتر contract داخلی با سرویس AI هستند، نه endpoint قابل استفاده برای کلاینت frontend.
- چند API در لیست شما نام قدیمی یا اشتباه دارند و در backend با path جدیدتری پیاده‌سازی شده‌اند:
  - `soil-data/ndvi-health` -> `soil/health/ndvi-health`
  - `pest-disease/*` -> `pest-detection/*`
  - `weather/water-need-prediction` -> `water/need-prediction`
  - `soile/*` -> به صورت داخلی برای AI استفاده می‌شود، ولی route عمومی backend با `soil/*` است
