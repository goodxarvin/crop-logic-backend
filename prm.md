# گزارش بررسی معماری و پیاده سازی پروژه CropLogic

## دامنه بررسی

- این بررسی فقط روی کد موجود در ریپازیتوری انجام شد.
- طبق درخواست شما هیچ تغییری در کد اپلیکیشن داده نشد.
- برای این گزارش تست اجرایی سراسری اجرا نشد؛ جمع بندی بر پایه بازبینی ساختار، تنظیمات، مدل ها، ویوها، سرویس ها و تست های موجود است.

## جمع بندی سریع

پروژه از نظر تفکیک دامنه ها به چند اپ Django ساختار قابل فهمی دارد، اما چند ضعف جدی در مرزهای معماری، امنیت APIها، پایداری در کار با سرویس های خارجی، و یکپارچگی داده ها دیده می شود. مهم ترین ریسک ها این ها هستند:

1. سیستم نوتیفیکیشن از نظر مجوزدهی ناامن است و کاربر احراز هویت شده می تواند به کانال دلخواه subscribe/publish کند.
2. ویرایش سنسورهای مزرعه باعث حذف و بازسازی کامل سنسورها می شود و به خاطر `CASCADE` شدن، تاریخچه داده های سنسور هم از بین می رود.
3. ساخت مزرعه و زون بندی، dispatch تسک های async را قبل از commit نهایی تراکنش بالادستی شروع می کند و مستعد race condition است.
4. چند API وابسته به سرویس خارجی، خطاهای شبکه/پیکربندی را handle نمی کنند و به احتمال زیاد با 500 خام fail می شوند.

### 3) dispatch تسک های زون بندی داخل جریان تراکنش بالادستی انجام می شود

شدت: بالا

شواهد:

- در `farm_hub/services.py:19` تا `farm_hub/services.py:23` ساخت مزرعه داخل `transaction.atomic()` انجام می شود.
- همانجا `dispatch_farm_zoning` صدا زده می شود.
- در `crop_zoning/services.py:897` تا `crop_zoning/services.py:935` بعد از ساخت `CropArea` و `CropZone`ها، تابع `dispatch_zone_processing_tasks` اجرا می شود.

اثر:

- `create_zones_and_dispatch` داخل یک atomic داخلی صدا زده می شود، اما هنوز transaction بیرونی `create_farm_with_zoning` commit نشده است.
- worker ممکن است قبل از commit نهایی شروع شود و داده های وابسته را نبیند یا وضعیت ناقص ببیند.
- این مشکل در محیط های واقعی، intermittent و سخت برای دیباگ خواهد بود.

پیشنهاد:

- dispatch تسک ها باید با `transaction.on_commit(...)` انجام شود.
- ساخت entityها و شروع پردازش async باید کاملا از هم جدا شوند.
- بهتر است workflow ایجاد مزرعه -> commit -> enqueue zoning -> poll status به صورت صریح طراحی شود.

### 4) وابستگی به سرویس خارجی در چند endpoint بدون fail-safe مناسب است

شدت: بالا

شواهد:

- `dashboard/views.py:126` تا `dashboard/views.py:134`
- `irrigation_recommendation/views.py:63` تا `irrigation_recommendation/views.py:79`
- `irrigation_recommendation/views.py:125` تا `irrigation_recommendation/views.py:136`
- `fertilization_recommendation/views.py:63` تا `fertilization_recommendation/views.py:80`
- `fertilization_recommendation/views.py:94` تا `fertilization_recommendation/views.py:105`
- در `external_api_adapter/adapter.py:50` و `external_api_adapter/adapter.py:70` خطاهای config/network به `ExternalAPIRequestError` تبدیل می شوند، اما endpoint های بالا آن را catch نمی کنند.

اثر:

- اگر `base_url` تنظیم نشده باشد یا شبکه/سرویس خارجی down باشد، پاسخ API داخلی احتمالا 500 خام می شود.
- رفتار endpoint ها ناهمگون است: مثلا `farm_ai_assistant` این خطا را handle می کند، اما dashboard/irrigation/fertilization نه.
- این ناهمگونی نگهداری و مانیتورینگ را سخت می کند.

پیشنهاد:

- یک لایه مشترک برای map کردن خطاهای external dependency به 502/503 ایجاد شود.
- همه endpoint های adapter-based رفتار یکسان داشته باشند.
- timeout، retry policy، circuit breaker و logging ساختاریافته برای این لایه لازم است.

### 5) GET مربوط به crop zoning دارای side effect است

شدت: متوسط رو به بالا

شواهد:

- در `crop_zoning/views.py:57` تا `crop_zoning/views.py:68` endpoint `GET /area/` فقط read نیست.
- در `crop_zoning/services.py:869` تا `crop_zoning/services.py:892` این GET می تواند:
  - area جدید بسازد
  - zone بسازد
  - rule-based data تولید کند
  - task جدید dispatch کند

اثر:

- semantics REST شکسته می شود؛ GET دیگر safe/read-only نیست.
- cache کردن، replay، tracing و حتی load-testing این endpoint رفتار غیرمنتظره پیدا می کند.
- اگر frontend چند بار polling کند، endpoint read عملا orchestration engine می شود.

پیشنهاد:

- endpoint creation/recompute باید POST باشد.
- GET فقط باید status/result را برگرداند.
- orchestration crop zoning بهتر است state machine یا task-oriented API شفاف داشته باشد.

### 7) خطای یکتایی email در update پروفایل می تواند 500 بدهد

شدت: متوسط

شواهد:

- در `account/views.py:53` تا `account/views.py:60` فیلدهای کاربر مستقیم set و save می شوند.
- مدل `User` در `account/models.py` ایمیل unique دارد.
- در این مسیر هیچ `IntegrityError`ی handle نشده است.

اثر:

- اگر کاربر ایمیلی را بگذارد که قبلا ثبت شده، به جای خطای business-level، احتمالا 500 برمی گردد.
- تجربه API ناهمگون می شود، چون در `RegisterView` برای uniqueness handling وجود دارد ولی در profile update نه.

پیشنهاد:

- validation uniqueness باید در serializer انجام شود.
- `save()` هم باید با handling مناسب برای race condition همراه باشد.

### 8) ingestion سنسور به availability سرویس نوتیفیکیشن گره خورده است

شدت: متوسط

شواهد:

- در `external_sensor_api/views.py:53` تا `external_sensor_api/views.py:80` ابتدا reading در DB ذخیره می شود و بعد `publish_notification` صدا زده می شود.
- در `notifications/services.py:24` تا `notifications/services.py:25` publish بدون try/except انجام می شود.

اثر:

- اگر Redis قطع باشد، ingest ممکن است بعد از ذخیره شدن داده با exception fail کند.
- نتیجه می تواند پاسخ 500 به sender باشد، در حالی که reading واقعا ثبت شده است.
- این باعث رفتار non-idempotent و retry خطرناک می شود: فرستنده دوباره retry می کند و رکورد duplicate می سازد.

پیشنهاد:

- publish notification باید best-effort و جدا از مسیر اصلی ingestion باشد.
- برای sensor ingest بهتر است notification async شود.
- اگر notification شکست خورد، ثبت reading نباید rollback منطقی API را مخدوش کند.

### 9) طراحی authentication برای OTP در مقیاس چند پردازه/چند نود پایدار نیست

شدت: متوسط

شواهد:

- در `config/settings.py:110` تا `config/settings.py:115` cache از نوع `LocMemCache` است.
- منطق OTP در `auth/views.py` از cache برای نگهداری کد استفاده می کند.
- هرچند routeهای OTP در `auth/urls.py:8` تا `auth/urls.py:9` فعلا کامنت شده اند، طراحی فعلی برای production-ready بودن کافی نیست.

اثر:

- در deployment چند worker یا چند instance، درخواست `request-otp` و `verify-otp` ممکن است به نودهای مختلف بخورند و verify شکست بخورد.
- این یعنی طراحی احراز هویت به process-local memory وابسته است.

پیشنهاد:

- cache/shared store مثل Redis برای OTP استفاده شود.
- rate limit، lockout، replay protection و audit logging هم به این flow اضافه شود.

### 10) نشانه های واضحی از ناتمام بودن مرزهای API و drift بین کد و قرارداد وجود دارد

شدت: متوسط

شواهد:

- routeهای مهمی کامنت شده اند: `auth/urls.py:8` تا `auth/urls.py:9`، `account/urls.py:7` تا `account/urls.py:8`، `crop_zoning/urls.py:16` تا `crop_zoning/urls.py:31`، `farm_ai_assistant/urls.py:15`
- کلاس ها و viewهای مرتبط هنوز در کد حضور دارند، اما publicly exposed نیستند.

اثر:

- فهمیدن وضعیت واقعی featureها برای توسعه دهنده جدید سخت می شود.
- schema و مستندات ممکن است با قابلیت واقعی محصول همگام نباشد.
- این وضعیت معمولا نشانه این است که API lifecycle و deprecation strategy شفاف نیست.

پیشنهاد:

- featureهای غیرفعال یا باید حذف شوند، یا با feature flag و مستندات واضح مدیریت شوند.
- برای endpointهای deprecated یا موقت، policy مشخص publish/unpublish لازم است.

## ضعف های معماری کلان

### 1) تکرار زیاد منطق دسترسی به مزرعه

در چند اپ مختلف mixin مشابه برای resolve کردن `farm_uuid` و ownership تکرار شده:

- `dashboard/views.py:20`
- `irrigation_recommendation/views.py:24`
- `fertilization_recommendation/views.py:24`
- `farm_ai_assistant/views.py:28`
- `farm_hub/views.py:16`
- `access_control/views.py:15`

اثر:

- رفتار خطاها یکدست نیست.
- هر اپ interpretation متفاوتی از “farm not found / access denied / validation error” دارد.
- تغییر policy ownership یا prefetching باید در چند نقطه تکرار شود.

پیشنهاد:

- یک service/mixin/shared permission مشترک برای farm-scoped access ساخته شود.

### 2) مرز بین دامنه های business و integration واضح نیست

نمونه ها:

- viewها مستقیم با `external_api_request(...)` کار می کنند.
- persistence، orchestration، و response-shaping در یک متد جمع شده است.
- در crop zoning هم business logic سنگین، persistence و async dispatch در یک service بزرگ متمرکز شده است.

اثر:

- تست واحد سخت تر می شود.
- وابستگی به provider خارجی به لایه API نشت کرده است.
- refactor یا جایگزینی provider بیرونی پرهزینه تر می شود.

پیشنهاد:

- use-case/service layer مشخص برای هر دامنه تعریف شود.
- adapter خارجی فقط در لایه integration بماند.
- view صرفا orchestration نهایی HTTP را انجام دهد.

## وضعیت تست ها

تست برای بعضی اپ ها وجود دارد، اما پوشش پروژه ناهمگن است. بر اساس ساختار فعلی، این اپ ها فاقد فایل تست قابل مشاهده هستند:

- `access_control`
- `account`
- `auth`
- `external_api_adapter`
- `fertilization_recommendation`
- `irrigation_recommendation`
- `plant_simulator`
- `pest_detection`
- `sensor_ingest`

این شکاف مخصوصا برای بخش های زیر نگران کننده است:

- مجوزدهی و access control
- authentication
- integration با سرویس خارجی
- رفتار خطا و fallback
- data integrity سنسورها و readingها

## اولویت پیشنهادی برای اصلاح

### فوری

1. بستن ضعف امنیتی notification stream/publish
2. جلوگیری از delete شدن سنسورها در update و حفظ تاریخچه reading
3. انتقال dispatch تسک ها به `transaction.on_commit`
4. یکسان سازی خطاهای external service و جلوگیری از 500 خام

### بعدی

1. جدا کردن endpointهای mock از API اصلی
2. حذف side effect از GETهای crop zoning
3. یکپارچه سازی farm access logic
4. افزودن تست برای auth, access_control, recommendations, integrations

## نتیجه نهایی

پروژه از نظر تقسیم اپ ها و شفاف بودن domain names شروع خوبی دارد، اما هنوز چند بخش مهم آن بیشتر شبیه نسخه integration-heavy و نیمه محصولی است تا یک backend production-hardened. بزرگ ترین ریسک های فعلی مربوط به:

- امنیت notificationها
- از دست رفتن داده در lifecycle سنسورها
- race condition در zoning async flow
- ناپایداری در برابر خطاهای سرویس های خارجی

اگر بخواهم فقط یک جمع بندی کوتاه بدهم: مشکل اصلی پروژه نه در syntax یا ساختار فایل ها، بلکه در مرزبندی responsibilityها، lifecycle داده ها، و رفتار fail-safe سیستم است.
