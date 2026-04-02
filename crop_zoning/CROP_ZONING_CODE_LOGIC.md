# Crop Zoning Code Logic

این فایل یک توضیح کامل و شفاف از منطق سه فایل زیر است:

- `crop_zoning/views.py`
- `crop_zoning/services.py`
- `crop_zoning/tests.py`

هدف این داکیومنت این است که بدون نیاز به خواندن مستقیم کد، بتوان فهمید هر endpoint چه می‌کند، داده‌ها چگونه ساخته می‌شوند، taskها چگونه مدیریت می‌شوند، و تست‌ها چه رفتارهایی را پوشش می‌دهند.

---

## تصویر کلی ماژول

ماژول `crop_zoning` برای این ساخته شده که:

1. یک polygon مربوط به زمین را دریافت یا پیدا کند.
2. آن را به چند zone مربعی تقسیم کند.
3. برای هر zone داده اولیه تولید کند.
4. برای هر zone یک task پردازش جداگانه ثبت کند.
5. خروجی مناسب برای فرانت برگرداند تا هم وضعیت پردازش را بداند و هم zoneها را روی نقشه نمایش دهد.

این ماژول دو نوع داده برای zoneها دارد:

- داده اولیه و rule-based که سریع ساخته می‌شود و برای خالی نبودن UI استفاده می‌شود.
- داده تحلیلی که بعدا از طریق task و داده خاک تکمیل می‌شود.

---

## منطق `crop_zoning/views.py`

فایل `views.py` فقط لایه HTTP است.
یعنی کار اصلی را خودش انجام نمی‌دهد، بلکه:

- ورودی request را می‌خواند
- آن را validate می‌کند یا به serviceها می‌سپارد
- خروجی مناسب را به صورت JSON response برمی‌گرداند

### 1) `AreaView`

این مهم‌ترین endpoint ماژول است.

### کار این view

- `farm_uuid` را از query params می‌گیرد.
- `page` و `page_size` را هم از query params می‌گیرد.
- از service می‌خواهد مطمئن شود برای این sensor یک area معتبر و zoneهای آن وجود دارند.
- اگر zoneها وجود نداشته باشند، ساخته می‌شوند.
- اگر taskهای پردازش لازم باشند، dispatch می‌شوند.
- در نهایت خروجی area + zoneهای همان صفحه + اطلاعات pagination را برمی‌گرداند.

### ورودی‌های `AreaView`

- `farm_uuid`: اجباری
- `page`: اختیاری، پیش‌فرض `1`
- `page_size`: اختیاری، پیش‌فرض `10`

### خروجی `AreaView`

خروجی سه بخش مهم دارد:

- `task`: وضعیت پردازش کل area
- `area`: polygon اصلی زمین
- `zones`: فقط zoneهای مربوط به همان صفحه
- `pagination`: اطلاعات صفحه‌بندی zoneها

### مدیریت خطا در `AreaView`

اگر هر کدام از این موارد رخ بدهد، خطای `400` داده می‌شود:

- `farm_uuid` ارسال نشده باشد
- `farm_uuid` معتبر نباشد یا farm پیدا نشود
- `page` نامعتبر باشد
- `page_size` نامعتبر باشد

اگر تنظیمات سمت سرور مشکل داشته باشند، خطای `500` داده می‌شود.

---

### 2) `ProductsView`

این endpoint لیست محصولات قابل کشت را برمی‌گرداند.

### کار این view

- از service می‌خواهد محصولات پیش‌فرض داخل دیتابیس sync شوند.
- سپس لیست محصولات را به فرمت مناسب فرانت برمی‌گرداند.

این view ساده است و منطق تحلیلی ندارد.

---

### 3) `ZonesInitialView`

این view برای ساخت zoneها از روی یک polygon ورودی استفاده می‌شود.

### کار این view

- polygon را از یکی از این کلیدها می‌گیرد:
  - `area`
  - `area_geojson`
  - `boundary`
- اگر هیچ‌کدام نباشد، از area پیش‌فرض mock استفاده می‌کند.
- در صورت ارسال، `cell_side_km` را هم می‌گیرد.
- service را صدا می‌زند تا area و zoneها ساخته شوند.
- response اولیه zoneها را برمی‌گرداند.

### تفاوت با `AreaView`

- `AreaView` بر اساس `farm_uuid` کار می‌کند و وضعیت taskها را هم برمی‌گرداند.
- `ZonesInitialView` بیشتر برای ساخت اولیه zoneها از روی polygon مناسب است.

---

### 4) `ZonesWaterNeedView`

این view لایه نیاز آبی zoneها را برمی‌گرداند.

### کار این view

- از request، `zoneIds` را می‌گیرد.
- service را صدا می‌زند.
- برای هر zone، level و value و color مربوط به آب را برمی‌گرداند.

---

### 5) `ZonesSoilQualityView`

این view لایه کیفیت خاک zoneها را برمی‌گرداند.

### خروجی اصلی

برای هر zone:

- `level`
- `score`
- `color`

---

### 6) `ZonesCultivationRiskView`

این view لایه ریسک کشت zoneها را برمی‌گرداند.

### خروجی اصلی

برای هر zone:

- `level`
- `color`

---

### 7) `ZoneDetailsView`

این endpoint جزئیات یک zone را برمی‌گرداند.

### کار این view

- `zone_id` را از URL می‌گیرد.
- جزئیات recommendation آن zone را از service می‌خواند.
- اگر zone پیدا نشود، `404` برمی‌گرداند.

### خروجی اصلی

- crop پیشنهادی
- درصد تطابق
- نیاز آبی
- سود تخمینی
- reason
- criteria
- مساحت zone

---

## منطق `crop_zoning/services.py`

این فایل قلب اصلی ماژول است.
بیشتر منطق واقعی اینجا پیاده‌سازی شده.

برای فهم بهتر، این فایل را می‌توان به 8 بخش تقسیم کرد.

---

## بخش 1: تنظیمات و utilityهای اولیه

### ثابت‌ها

چند constant اصلی در ابتدای فایل تعریف شده‌اند:

- `DEFAULT_CELL_SIDE_KM`: اندازه پیش‌فرض ضلع هر zone
- `DEFAULT_ZONE_PAGE_SIZE`: تعداد پیش‌فرض zoneها در هر صفحه response
- `RULE_BASED_ALGORITHM`: نام الگوریتم rule-based
- `RULE_BASED_PRODUCTS`: داده اولیه محصولات و اطلاعات نمایشی آنها

### `get_default_cell_side_km()`

این تابع اندازه پیش‌فرض ضلع هر zone را مشخص می‌کند.

اولویت‌ها:

1. اگر `CROP_ZONE_CELL_SIDE_KM` در settings وجود داشته باشد، همان استفاده می‌شود.
2. اگر نبود، از `CROP_ZONE_CHUNK_AREA_SQM` استفاده می‌کند و از روی آن ضلع مربع را حساب می‌کند.
3. اگر هیچ‌کدام نباشند، از `DEFAULT_CELL_SIDE_KM` استفاده می‌شود.

### `get_task_stale_seconds()`

این تابع مشخص می‌کند بعد از چند ثانیه یک task ممکن است stale محسوب شود.
یعنی اگر task گیر کرده باشد، دوباره dispatch شود.

### `get_cell_side_km(cell_side_km=None)`

اگر کاربر اندازه zone را داده باشد، آن را validate می‌کند.
اگر نداده باشد، مقدار پیش‌فرض را برمی‌گرداند.

### `get_chunk_area_sqm(cell_side_km=None)`

مساحت zone را از روی ضلع آن حساب می‌کند:

- ضلع بر حسب کیلومتر دریافت می‌شود
- به متر تبدیل می‌شود
- مربع آن به عنوان مساحت zone برگردانده می‌شود

### `parse_positive_int(...)`

برای validate کردن پارامترهای عددی مثبت استفاده می‌شود.
الان برای `page` و `page_size` استفاده می‌شود.

### `get_zone_page_request_params(query_params)`

این تابع پارامترهای pagination را از query params می‌گیرد:

- `page`
- `page_size`

اگر ارسال نشده باشند، از default استفاده می‌کند.
اگر نامعتبر باشند، `ValueError` می‌دهد.

---

## بخش 2: آماده‌سازی polygon و محاسبات هندسی

این بخش مسئول کار با GeoJSON و polygon است.

### `get_default_area_feature()`

یک area پیش‌فرض از داده mock برمی‌گرداند.

### `normalize_area_feature(area_feature)`

این تابع ورودی area را normalize می‌کند تا همیشه ساختار `Feature` داشته باشد.

### کارهای این تابع

- بررسی می‌کند ورودی null نباشد
- بررسی می‌کند ورودی dict باشد
- اگر ورودی از نوع `Feature` نباشد، آن را به `Feature` تبدیل می‌کند
- بررسی می‌کند geometry از نوع `Polygon` باشد
- بررسی می‌کند polygon حداقل 4 نقطه داشته باشد

### `get_polygon_ring(area_feature)`

حلقه اصلی polygon را استخراج می‌کند.

### `polygon_area_sqm(ring)`

مساحت polygon را به متر مربع حساب می‌کند.
برای این کار نقاط جغرافیایی را به مختصات مسطح تقریبی تبدیل می‌کند و فرمول shoelace را اجرا می‌کند.

### `normalize_points(ring)`

اگر آخر polygon با نقطه اول بسته شده باشد، نقطه تکراری آخر را حذف می‌کند.

### `calculate_center(points)`

مرکز تقریبی polygon یا مربع را از میانگین نقاط حساب می‌کند.

### `get_bbox(points)`

کمینه و بیشینه طول و عرض جغرافیایی را برمی‌گرداند تا محدوده کلی polygon مشخص شود.

### `meters_to_latitude_delta(meters)` و `meters_to_longitude_delta(meters, latitude)`

این دو تابع فاصله متر را به اختلاف latitude و longitude تبدیل می‌کنند.
برای ساخت grid مربعی از این دو تابع استفاده می‌شود.

---

## بخش 3: تشخیص برخورد polygon و cell

این بخش مشخص می‌کند که آیا یک مربع grid واقعا با polygon زمین برخورد دارد یا نه.

### `point_in_polygon(point, polygon_points)`

چک می‌کند یک نقطه داخل polygon هست یا نه.

### `_orientation`, `_on_segment`, `segments_intersect`

این توابع utilityهای هندسی برای تشخیص برخورد دو خط هستند.

### `rectangle_contains_point(point, cell_points)`

چک می‌کند یک نقطه داخل مربع cell قرار دارد یا نه.

### `polygon_intersects_cell(polygon_points, cell_points)`

این مهم‌ترین تابع تقاطع است.
اگر یکی از شرایط زیر برقرار باشد، cell معتبر در نظر گرفته می‌شود:

- مرکز cell داخل polygon باشد
- یکی از گوشه‌های cell داخل polygon باشد
- یکی از نقاط polygon داخل cell باشد
- یکی از اضلاع polygon با اضلاع cell برخورد داشته باشد

نتیجه: فقط مربع‌هایی zone می‌شوند که واقعا با زمین هم‌پوشانی داشته باشند.

---

## بخش 4: ساخت zoneها از روی area

### `build_square_points(...)`

چهار گوشه یک مربع را از روی مرزهای آن می‌سازد.

### `build_zone_square(area_points, center, zone_area_sqm)`

اگر area خیلی کوچک باشد یا zoneی تولید نشود، یک مربع fallback حول center area ساخته می‌شود.

### `split_area_into_zones(area_feature, cell_side_km=None)`

این تابع مهم‌ترین بخش ساخت zoneها است.

### مراحل اجرای آن

1. polygon area را می‌گیرد.
2. center و bbox و total area را حساب می‌کند.
3. اندازه ضلع zone را مشخص می‌کند.
4. روی bbox یک grid مربعی می‌سازد.
5. هر cell را با `polygon_intersects_cell` بررسی می‌کند.
6. اگر cell با polygon تقاطع داشته باشد، یک zone جدید می‌سازد.
7. برای هر zone این داده‌ها تولید می‌شود:
   - `zone_id`
   - `geometry`
   - `points`
   - `center`
   - `area_sqm`
   - `area_hectares`
   - `sequence`
8. اگر هیچ zoneی ساخته نشود، یک zone fallback می‌سازد.
9. در نهایت area summary و لیست zoneها را برمی‌گرداند.

### نکته مهم

در این پروژه zoneها grid-based هستند، نه بر اساس تقسیم واقعی shape زمین.
یعنی ابتدا grid مربعی ساخته می‌شود و بعد فقط مربع‌هایی که با زمین برخورد دارند نگه داشته می‌شوند.

---

## بخش 5: تولید recommendation و لایه‌های تحلیلی

این بخش داده پیشنهادی هر zone را تولید می‌کند.

### `build_rule_based_zone_metrics(index, coords)`

این تابع بدون نیاز به API خارجی، برای هر zone یک recommendation اولیه می‌سازد.

### هدف آن

وقتی zone تازه ساخته می‌شود، فرانت از همان ابتدا داده خالی نداشته باشد.

### خروجی آن

- `recommended_crop`
- `match_percent`
- `water_need_level`
- `water_need_value`
- `soil_quality_score`
- `soil_level`
- `cultivation_risk_level`
- `estimated_profit`
- `reason`
- `criteria`

این داده‌ها از روی مختصات zone و `sequence` به صورت deterministic ساخته می‌شوند.

### `build_initial_zone_payload(zone)`

خروجی سبک و اولیه برای endpoint ساخت zoneها تولید می‌کند.

### `build_area_zone_payload(zone)`

خروجی کامل‌تر برای `AreaView` تولید می‌کند و این بخش‌ها را شامل می‌شود:

- geometry
- center
- area
- processing status
- crop recommendation
- water layer
- soil layer
- risk layer

### `persist_zone_analysis_metrics(zone, metrics)`

metrics را داخل مدل‌های مختلف ذخیره می‌کند:

- recommendation
- criteria
- water need layer
- soil quality layer
- cultivation risk layer

### `ensure_rule_based_zone_data(zone, force=False)`

اگر zone هنوز recommendation نداشته باشد، با rule-based data آن را پر می‌کند.

---

## بخش 6: تحلیل خاک واقعی و ذخیره نتیجه

### `_get_level_color_map(...)`

رنگ هر level را برای سه لایه water / soil / risk برمی‌گرداند.

### `_pick_level(...)`

از روی score مشخص می‌کند level برابر `low` یا `medium` یا `high` است.

### `_format_range(...)`

برای ساخت رشته‌هایی مثل `3000-4000 m³/ha` استفاده می‌شود.

### `_derive_analysis_metrics(depths)`

این تابع از داده depthهای خاک، recommendation نهایی را می‌سازد.

### ورودی آن

آرایه‌ای از depthها که از سرویس خارجی خاک می‌آید.

### محاسبات مهم آن

از میانگین این فیلدها استفاده می‌کند:

- `phh2o`
- `soc`
- `clay`
- `nitrogen`
- `wv0033`

بعد از اینها محاسبه می‌شود:

- کیفیت خاک
- نیاز آبی
- ریسک کشت
- محصول پیشنهادی
- درصد تطابق
- reason
- criteria

### `fetch_soil_data_for_zone(zone)`

برای یک zone به سرویس خارجی AI درخواست می‌زند و داده خاک می‌گیرد.

### payload ارسالی

- longitude
- latitude
- geometry zone
- center
- area

### `analyze_and_store_zone_soil_data(zone_id)`

این تابع منطق اصلی پردازش هر zone در worker است.

### مراحل آن

1. zone از دیتابیس خوانده می‌شود.
2. اگر قبلا کامل شده باشد، دوباره کاری نمی‌کند.
3. status روی `processing` می‌رود.
4. از API خارجی داده خاک می‌گیرد.
5. depthها را استخراج می‌کند.
6. recommendation واقعی‌تر را از روی خاک می‌سازد.
7. نتیجه را داخل مدل‌های analysis و recommendation ذخیره می‌کند.
8. status را `completed` می‌کند.
9. اگر هر خطایی رخ دهد، status روی `failed` می‌رود و متن خطا ذخیره می‌شود.

---

## بخش 7: مدیریت taskهای zone

چون هر zone جداگانه پردازش می‌شود، باید taskها مدیریت شوند.

### `_get_stale_zone_ids(zones)`

این تابع zoneهایی را پیدا می‌کند که task آنها stale شده است.

### چه zoneهایی stale محسوب می‌شوند؟

- zone کامل نشده باشد
- task_id داشته باشد
- task خیلی قدیمی شده باشد
- یا task_id آن با task یک zone completed مشترک باشد
- یا state task در celery یکی از stateهای نامعتبر برای ادامه باشد

### `dispatch_zone_processing_tasks(crop_area_id=None, zone_ids=None, force=False)`

این تابع برای zoneهای انتخاب‌شده task celery ثبت می‌کند.

### رفتار آن

- zoneهای completed را رد می‌کند
- اگر zone pending/processing باشد و task_id معتبر داشته باشد، دوباره dispatch نمی‌کند مگر `force=True`
- برای هر zone یک task جدا ثبت می‌کند
- اگر celery broker در دسترس نباشد، باز هم یک `task_id` محلی تولید می‌کند
- متن خطا را در `processing_error` ذخیره می‌کند

### اهمیت این طراحی

این باعث می‌شود:

- هر zone مستقل پردازش شود
- fail شدن یک zone بقیه را متوقف نکند
- فرانت بتواند وضعیت هر zone را جدا ببیند

---

## بخش 8: ساخت area، بازیابی area و ساخت payload response

### `create_missing_zones_for_area(crop_area)`

اگر area در دیتابیس وجود داشته باشد ولی zoneهایش از بین رفته باشند یا ساخته نشده باشند، دوباره از روی geometry آن zoneها را می‌سازد.

### `get_farm_for_uuid(farm_uuid)`

اعتبارسنجی می‌کند که:

- `farm_uuid` ارسال شده باشد
- farm واقعا در دیتابیس وجود داشته باشد

### `ensure_latest_area_ready_for_processing(farm_uuid, area_feature=None)`

این یکی از مهم‌ترین توابع کل فایل است.

### منطق آن

1. sensor را پیدا می‌کند.
2. آخرین area مربوط به آن sensor را می‌گیرد.
3. اگر area وجود نداشته باشد:
   - area پیش‌فرض یا area ورودی را می‌گیرد
   - area و zoneها را می‌سازد
   - taskها را dispatch می‌کند
4. اگر area وجود داشته باشد:
   - مطمئن می‌شود zoneها وجود دارند
   - برای هر zone، rule-based data را در صورت نبود ایجاد می‌کند
   - zoneهای stale را پیدا می‌کند
   - zoneهای لازم را دوباره dispatch می‌کند
   - area تازه از دیتابیس خوانده می‌شود و برگردانده می‌شود

### نتیجه این تابع

وقتی `AreaView` این تابع را صدا می‌زند، همیشه یک area آماده برای نمایش و پردازش دارد.

### `create_zones_and_dispatch(area_feature, cell_side_km=None, sensor=None)`

این تابع area جدید را می‌سازد.

### مراحل آن

1. productها sync می‌شوند.
2. area normalize می‌شود.
3. area به zoneها تقسیم می‌شود.
4. داخل transaction:
   - یک `CropArea` ساخته می‌شود
   - همه `CropZone`ها bulk create می‌شوند
5. zoneها دوباره از دیتابیس خوانده می‌شوند
6. rule-based data برای هر zone ساخته می‌شود
7. taskهای پردازش dispatch می‌شوند
8. area و zones برگردانده می‌شوند

### `_zones_queryset(zone_ids=None)`

یک queryset آماده برمی‌گرداند که relationهای لازم را از قبل load می‌کند:

- recommendation
- product
- criteria
- water layer
- soil layer
- risk layer

این باعث می‌شود responseسازی سریع‌تر و با query کمتر انجام شود.

### `get_latest_area_payload(area=None, page=1, page_size=DEFAULT_ZONE_PAGE_SIZE)`

این تابع خروجی نهایی `AreaView` را می‌سازد.

### کارهای این تابع

1. area را پیدا می‌کند.
2. وضعیت همه zoneها را می‌خواند.
3. تعداد completed / pending / processing / failed را حساب می‌کند.
4. `task.status` را تعیین می‌کند.
5. `stage` و `stage_label` را تعیین می‌کند.
6. درصد پیشرفت را حساب می‌کند.
7. zoneهای همان صفحه را با slicing برمی‌دارد.
8. `pagination` را می‌سازد.
9. payload نهایی را برمی‌گرداند.

### منطق `task.status`

- اگر zone failed داشته باشیم: `FAILURE`
- اگر همه complete باشند: `SUCCESS`
- اگر بخشی complete یا processing باشند: `PROCESSING`
- در غیر این صورت: `PENDING`

### منطق pagination

- `page` و `page_size` از request گرفته می‌شوند
- `total_pages` از تقسیم تعداد کل zoneها بر `page_size` محاسبه می‌شود
- فقط zoneهای همان بازه برگردانده می‌شوند
- اطلاعات page فعلی، تعداد صفحات و وجود صفحه قبل/بعد در body قرار می‌گیرد

### `get_initial_zones_payload(crop_area)`

payload ساده‌تر برای endpoint اولیه zoneها می‌سازد.

### `get_water_need_payload(zone_ids=None)`

خروجی لایه نیاز آبی را برمی‌گرداند.

### `get_soil_quality_payload(zone_ids=None)`

خروجی لایه کیفیت خاک را برمی‌گرداند.

### `get_cultivation_risk_payload(zone_ids=None)`

خروجی لایه ریسک کشت را برمی‌گرداند.

### `get_zone_details_payload(zone_id)`

خروجی دیتیل یک zone را می‌سازد.

---

## جریان کامل اجرای `GET /api/crop-zoning/area/`

اگر بخواهیم کل flow را از ابتدا تا انتها خیلی ساده توضیح بدهیم:

1. فرانت `farm_uuid` و احتمالا `page` و `page_size` را می‌فرستد.
2. `AreaView` پارامترها را می‌خواند.
3. `ensure_latest_area_ready_for_processing` اجرا می‌شود.
4. اگر area وجود نداشته باشد، area و zoneها ساخته می‌شوند.
5. اگر zoneها ناقص باشند، کامل می‌شوند.
6. اگر recommendation اولیه نباشد، ساخته می‌شود.
7. اگر taskهای لازم وجود نداشته باشند یا stale باشند، dispatch می‌شوند.
8. `get_latest_area_payload` اجرا می‌شود.
9. وضعیت کلی task و zoneهای صفحه فعلی ساخته می‌شود.
10. response نهایی به فرانت برمی‌گردد.

---

## منطق `crop_zoning/tests.py`

این فایل تست رفتار کلیدی API را پوشش می‌دهد.

تست‌ها با `Django TestCase` و `APIRequestFactory` نوشته شده‌اند.

### تنظیمات مشترک تست‌ها

در تست‌ها از این تنظیمات استفاده شده:

- `USE_EXTERNAL_API_MOCK=True`
- `CROP_ZONE_CHUNK_AREA_SQM=200000`

هدف این است که:

- وابستگی به API خارجی واقعی حذف شود
- zoneها با اندازه مشخص و قابل پیش‌بینی ساخته شوند

---

## کلاس `ZonesInitialViewTests`

### `test_post_accepts_area_geojson_alias`

این تست بررسی می‌کند که اگر polygon با کلید `area_geojson` ارسال شود:

- endpoint آن را قبول کند
- پاسخ `200` بدهد
- zone ساخته شود
- تعداد zoneهای خروجی با `zone_count` یکسان باشد

این تست در عمل alias بودن `area_geojson` را validate می‌کند.

---

## کلاس `AreaViewTests`

این کلاس رفتارهای اصلی `AreaView` را تست می‌کند.

### `setUp`

در شروع هر تست:

- یک user ساخته می‌شود
- یک sensor برای آن user ساخته می‌شود
- `APIRequestFactory` آماده می‌شود

### `_create_area(...)`

یک helper برای ساخت سریع `CropArea` در تست‌ها است.

### `_request()`

یک request استاندارد برای `AreaView` با `farm_uuid` معتبر می‌سازد.

### `_request_with_pagination(page, page_size)`

یک request برای تست pagination می‌سازد.

---

### تست‌های اصلی `AreaView`

#### `test_get_requires_farm_uuid`

بررسی می‌کند اگر `farm_uuid` ارسال نشود، پاسخ `400` برگردد.

#### `test_get_returns_pending_task_status_until_all_zones_complete`

بررسی می‌کند اگر zoneها pending و processing باشند:

- status کلی `PROCESSING` باشد
- area برگردد
- zoneها در response باشند
- فیلد `processing_status` برای zone موجود باشد

#### `test_get_returns_area_when_all_tasks_complete`

بررسی می‌کند وقتی همه zoneها complete باشند:

- status کلی `SUCCESS` باشد
- zoneها برگردند
- فیلدهای recommendation و layerها موجود باشند

#### `test_get_returns_paginated_zones`

تست جدید pagination است.

بررسی می‌کند که:

- با `page=2` و `page_size=1`
- فقط zone دوم برگردد
- اطلاعات pagination درست باشد
- `total_pages`, `has_next`, `has_previous` درست باشند

#### `test_get_rejects_invalid_pagination_params`

بررسی می‌کند اگر `page=0` باشد:

- پاسخ `400` بدهد
- پیام خطا مناسب برگردد

#### `test_get_dispatches_zone_task_when_task_id_is_missing`

با mock کردن `dispatch_zone_processing_tasks` بررسی می‌کند که:

- اگر zone task_id نداشته باشد
- در زمان فراخوانی `AreaView`
- dispatch انجام شود

#### `test_get_creates_area_when_sensor_has_no_data`

با mock کردن `create_zones_and_dispatch` بررسی می‌کند که:

- اگر sensor هنوز area نداشته باشد
- سیستم area جدید بسازد
- همان sensor را به service پاس بدهد

#### `test_each_zone_gets_its_own_task`

بررسی می‌کند برای دو zone جدا:

- دو task مستقل ایجاد شود
- هر zone task_id جدا داشته باشد

این تست خیلی مهم است چون تایید می‌کند taskها shared نیستند و per-zone هستند.

#### `test_get_generates_local_task_id_when_broker_is_unavailable`

با mock کردن celery و ایجاد `OperationalError` بررسی می‌کند که:

- حتی وقتی broker در دسترس نیست
- سیستم task_id محلی بسازد
- response خراب نشود
- وضعیت کلی درست بماند

#### `test_get_stores_task_id_and_reuses_it_on_next_request`

بررسی می‌کند:

- وقتی اولین request task_id را ثبت کرد
- request بعدی دوباره task تازه نسازد
- همان task_id قبلی reuse شود

این تست جلوی dispatch تکراری را می‌گیرد.

#### `test_get_redispatches_pending_zone_when_shared_task_already_completed`

این تست سناریوی قدیمی یا خراب را پوشش می‌دهد.

سناریو:

- یک zone completed شده
- zone دیگر pending مانده
- هر دو task_id یکسان دارند

در این حالت سیستم باید zone stale را دوباره dispatch کند.

این تست نشان می‌دهد منطق stale detection واقعا کار می‌کند.

---

## جمع‌بندی معماری

اگر خیلی خلاصه بخواهیم نقش هر فایل را بگوییم:

### `views.py`

لایه HTTP است.

- request را می‌گیرد
- service مناسب را صدا می‌زند
- response برمی‌گرداند

### `services.py`

لایه business logic است.

- area را validate می‌کند
- polygon را به zone تبدیل می‌کند
- recommendation اولیه و نهایی می‌سازد
- taskها را مدیریت می‌کند
- payload response را می‌سازد

### `tests.py`

لایه اطمینان از رفتار سیستم است.

- ساخت area
- ساخت zone
- status task
- dispatch task
- stale task
- pagination
- خطاهای ورودی

را تست می‌کند.

---

## نکات مهم برای فرانت

- endpoint `area` الان pagination دارد و `zones` همیشه همه zoneها را برنمی‌گرداند.
- تعداد کل zoneها از `task.total_zones` یا `pagination.total_zones` قابل خواندن است.
- تعداد کل صفحه‌ها از `pagination.total_pages` قابل خواندن است.
- برای نمایش progress باید از `task.progress_percent` و `task.status` استفاده شود.
- `task.status` وضعیت کلی area است، نه وضعیت تک‌تک zoneها.
- وضعیت هر zone داخل `processing_status` قرار دارد.
- در صورت نیاز به جزئیات بیشتر برای یک zone باید `ZoneDetailsView` صدا زده شود.

---

## نکات مهم برای بک‌اند

- منطق grid سازی و پردازش zoneها تقریبا کامل داخل `services.py` متمرکز شده است.
- `AreaView` عمدا thin نگه داشته شده تا business logic وارد view نشود.
- rule-based data نقش fallback سریع برای UI را دارد.
- data واقعی‌تر بعدا با taskهای تحلیل خاک جایگزین یا تکمیل می‌شود.
- تست‌ها بیشتر روی پایداری flow پردازش و task dispatch تمرکز دارند.

