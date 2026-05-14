# مستند کامل سیستم Access Control

این سند معماری، اجزای اصلی، جریان اجرا، مدل داده، تنظیمات، APIها و محدودیت های فعلی سیستم `access_control` را در بک اند CropLogic توضیح می دهد.

## هدف سیستم

سیستم `access_control` برای پاسخ به این سوال طراحی شده است:

- آیا یک کاربر روی یک مزرعه مشخص به یک قابلیت خاص دسترسی دارد یا نه؟
- این تصمیم بر چه اساسی گرفته می شود: پلن اشتراک، نوع مزرعه، محصول، سنسور، یا قوانین اختصاصی؟
- آیا این تصمیم باید در سطح کل route اعمال شود یا در سطح یک feature مشخص داخل view؟

این سیستم دو لایه اصلی دارد:

1. کنترل دسترسی در سطح route با `RouteFeatureAccessMiddleware`
2. کنترل دسترسی در سطح feature/view با `FeatureAccessPermission`

هسته تصمیم گیری نهایی هم از طریق سرویس OPA انجام می شود و بک اند نقش جمع آوری context، ارسال درخواست، cache کردن نتیجه و اعمال پاسخ را دارد.

---

## محل های اصلی پیاده سازی

فایل های مهم این سیستم:

- `access_control/models.py`
- `access_control/services.py`
- `access_control/permissions.py`
- `access_control/middleware.py`
- `access_control/views.py`
- `access_control/serializers.py`
- `access_control/urls.py`
- `config/feature.json`
- `config/settings.py`

فعال سازی سراسری در تنظیمات:

- `config/settings.py:75` -> اضافه شدن `access_control.middleware.RouteFeatureAccessMiddleware`
- `config/settings.py:145` -> اضافه شدن `access_control.permissions.FeatureAccessPermission` به `DEFAULT_PERMISSION_CLASSES`

این یعنی به صورت پیش فرض، تمام endpointهای DRF که anonymous نیستند، هم از نظر authentication و هم از نظر access control بررسی می شوند.

---

## اجزای دامنه داده

### 1) SubscriptionPlan

مدل `SubscriptionPlan` در `access_control/models.py` پلن اشتراک را نگه می دارد.

فیلدهای مهم:

- `code`: کد یکتا مثل `gold` یا `starter`
- `name`: نام نمایشی پلن
- `metadata`: داده های تکمیلی؛ مثلا تعیین پلن پیش فرض با `{"is_default": true}`
- `is_active`: فعال یا غیرفعال بودن پلن

کاربرد اصلی:

- اتصال مستقیم به `FarmHub.subscription_plan`
- استفاده در match شدن ruleها
- fallback برای مزارعی که پلن ندارند

### 2) AccessFeature

مدل `AccessFeature` قابلیت هایی را تعریف می کند که باید درباره آن ها تصمیم گیری شود.

فیلدهای مهم:

- `code`: شناسه یکتای feature مثل `farm_dashboard`
- `name`: نام خوانا
- `feature_type`: یکی از `page`، `widget` یا `action`
- `default_enabled`: وضعیت پیش فرض قبل از اعمال ruleها
- `metadata`: داده های توسعه پذیر

نکته مهم:

`default_enabled` نقطه شروع محاسبه است. بعد از آن ruleها می توانند وضعیت هر feature را تغییر دهند.

### 3) AccessRule

مدل `AccessRule` قانون های دسترسی را نگه می دارد.

فیلدهای مهم:

- `code`: شناسه یکتا برای rule
- `priority`: اولویت اجرا؛ عدد کمتر یعنی زودتر پردازش می شود
- `effect`: یکی از `allow` یا `deny`
- `features`: featureهایی که rule روی آن ها اثر می گذارد
- `subscription_plans`: محدودیت بر اساس پلن
- `farm_types`: محدودیت بر اساس نوع مزرعه
- `products`: محدودیت بر اساس محصول
- `sensor_catalogs`: محدودیت بر اساس کاتالوگ دستگاه/سنسور
- `metadata`: برای شرط های تکمیلی مثل `sensor_catalog_codes`

نکته رفتاری:

در `build_farm_access_profile` ruleها بر اساس `priority` و سپس `id` مرتب می شوند. اگر چند rule روی یک feature اثر بگذارند، ruleهای بعدی می توانند نتیجه قبلی را override کنند.

### 4) FarmAccessProfile

مدل `FarmAccessProfile` snapshot یا خروجی resolved شده دسترسی های یک مزرعه است.

فیلدهای مهم:

- `farm`: ارتباط one-to-one با `FarmHub`
- `subscription_plan`: پلنی که در نهایت برای resolve استفاده شده
- `profile_data`: خروجی نهایی شامل featureها و matched ruleها
- `resolved_from_profile`: فلگ کمکی

این مدل بیشتر برای materialize کردن وضعیت دسترسی مزرعه استفاده می شود تا بتوان نتیجه محاسبه را ذخیره و بازاستفاده کرد.

---

## ارتباط با FarmHub

در `farm_hub/models.py`، هر مزرعه (`FarmHub`) این contextها را دارد:

- `owner`
- `farm_type`
- `subscription_plan`
- `products`
- `sensors`

سیستم access control از همین context برای تصمیم گیری استفاده می کند. بنابراین دسترسی صرفا به user وابسته نیست؛ بلکه به ترکیب user + farm + ویژگی های مزرعه وابسته است.

---

## منطق پلن پیش فرض

تابع های مرتبط:

- `get_default_subscription_plan`
- `get_effective_subscription_plan`

منطق به این صورت است:

1. اگر خود مزرعه `subscription_plan` داشته باشد، همان استفاده می شود.
2. اگر نداشته باشد، اولین پلن فعال با `metadata.is_default=True` انتخاب می شود.
3. اگر چنین پلنی هم نبود، پلن `gold` از `access_control/catalog.py` fallback می شود.

این رفتار باعث می شود مزرعه بدون پلن صریح هم قابل authorize باشد.

---

## ساخت Access Profile داخل بک اند

تابع اصلی: `build_farm_access_profile` در `access_control/services.py`

### ورودی

یک آبجکت `FarmHub`

### مراحل اجرا

1. مزرعه با `select_related` و `prefetch_related` کامل reload می شود.
2. پلن موثر مزرعه با `get_effective_subscription_plan` تعیین می شود.
3. محصول های مزرعه و device catalogهای سنسورهای مزرعه جمع آوری می شوند.
4. تمام `AccessFeature`های فعال خوانده می شوند.
5. وضعیت اولیه هر feature از `default_enabled` ساخته می شود.
6. تمام `AccessRule`های فعال، به ترتیب `priority` بررسی می شوند.
7. هر rule با تابع `_match_rule` روی مزرعه match می شود.
8. اگر rule match شود:
   - به `matched_rules` اضافه می شود
   - featureهای مرتبط را `allow` یا `deny` می کند
   - `source` آن feature برابر کد rule می شود
9. نتیجه نهایی در `FarmAccessProfile` ذخیره می شود.
10. خروجی profile به caller برگردانده می شود.

### شرط های match شدن rule

تابع `_match_rule` این موارد را بررسی می کند:

- فعال بودن rule
- سازگاری پلن اشتراک
- سازگاری نوع مزرعه
- وجود حداقل یک product منطبق
- وجود حداقل یک sensor catalog منطبق
- وجود تقاطع با `metadata["sensor_catalog_codes"]`

### ساختار تقریبی خروجی profile

```json
{
  "farm_uuid": "...",
  "subscription_plan": {
    "uuid": "...",
    "code": "gold",
    "name": "Gold"
  },
  "features": {
    "farm_dashboard": {
      "name": "Farm Dashboard",
      "type": "page",
      "enabled": true,
      "source": "starter-dashboard-rule"
    }
  },
  "matched_rules": [
    {
      "code": "starter-dashboard-rule",
      "name": "Starter Dashboard Rule",
      "effect": "allow",
      "priority": 10
    }
  ],
  "resolved_from_profile": true
}
```

این خروجی بیشتر برای نمایش، debugging، یا ساخت viewهای profile-based مناسب است.

---

## کنترل دسترسی runtime با OPA

### ایده کلی

در زمان درخواست API، بک اند خودش ruleها را برای همه routeها نهایی نمی کند؛ بلکه context را به سرویس OPA می فرستد و جواب allow/deny می گیرد.

### چرا OPA؟

مزایا:

- جدا شدن policy از کد بک اند
- امکان تغییر ruleها بدون بازنویسی منطق اصلی viewها
- مناسب برای تصمیم گیری policy-based و context-aware

### تنظیمات OPA

در `config/settings.py`:

- `ACCESS_CONTROL_AUTHZ_ENABLED`
- `ACCESS_CONTROL_AUTHZ_BASE_URL`
- `ACCESS_CONTROL_AUTHZ_BATCH_PATH`
- `ACCESS_CONTROL_AUTHZ_TIMEOUT`
- `ACCESS_CONTROL_AUTHZ_CACHE_TIMEOUT`

مقدار پیش فرض base URL:

- `http://croplogic-accsess-opa:8181`

مسیر پیش فرض batch authorization:

- `/v1/data/croplogic/authz/batch_decision`

---

## ساخت payload برای OPA

تابع های مهم:

- `build_opa_user`
- `build_opa_resource`
- `build_authorization_input`

### build_opa_user

اطلاعات user را به فرم policy-friendly تبدیل می کند:

- `id`
- `username`
- `email`
- `phone_number`
- `is_staff`
- `is_superuser`
- `role` که فعلا ثابت و برابر `farmer` است

### build_opa_resource

اطلاعات مزرعه را به فرم resource برمی گرداند. اگر مزرعه وجود نداشته باشد، فیلدها با مقدارهای خالی برگردانده می شوند.

فیلدهای مهم resource:

- `farm_id`
- `subscription_plan_codes`
- `farm_types`
- `crop_types`
- `sensor_codes`
- `power_sensor`
- `customization`

نکته:

`power_sensor` از `sensor.power_source.type` استخراج می شود، اگر این ساختار به صورت dict ذخیره شده باشد.

### build_authorization_input

payload نهایی برای OPA را می سازد:

```json
{
  "user": {"...": "..."},
  "resource": {"...": "..."},
  "features": ["farm_dashboard", "notifications"],
  "action": "view",
  "route": "/api/dashboard/"
}
```

---

## درخواست batch به OPA

تابع اصلی: `request_opa_batch_authorization`

### رفتار

1. اگر `ACCESS_CONTROL_AUTHZ_ENABLED=false` باشد، برای همه featureها مقدار `true` برمی گرداند.
2. اگر لیست feature خالی باشد، پاسخ خالی برمی گرداند.
3. در غیر این صورت با `requests.post` به OPA درخواست می فرستد.
4. payload داخل کلید `input` ارسال می شود.
5. نتیجه از `response.json().get("result", {})` خوانده می شود.

### Error handling

اگر ارتباط با OPA fail شود:

- exception از نوع `requests.RequestException` گرفته می شود
- event لاگ می شود
- metric ثبت می شود
- خطای `AccessControlServiceUnavailable` بالا انداخته می شود

اگر OPA JSON نامعتبر برگرداند:

- metric `access_control.opa.invalid_json` ثبت می شود
- `AccessControlServiceUnavailable` برگردانده می شود

اگر `result` خالی باشد:

- metric `access_control.opa.empty_result` ثبت می شود
- warning لاگ می شود

---

## فرمت های پاسخ قابل قبول از OPA

تابع `normalize_opa_batch_result` چند نوع payload را پشتیبانی می کند:

### حالت 1: decisions

```json
{
  "decisions": {
    "farm_dashboard": true,
    "notifications": false
  }
}
```

### حالت 2: features با ساختار nested

```json
{
  "features": {
    "farm_dashboard": {"allow": true},
    "notifications": {"allow": false}
  }
}
```

### حالت 3: allowed_features

```json
{
  "allowed_features": ["farm_dashboard"]
}
```

### حالت 4: map ساده از booleanها

```json
{
  "farm_dashboard": true,
  "notifications": false
}
```

اگر payload خارج از این الگوها باشد، سیستم آن را unsupported تلقی می کند و `AccessControlServiceUnavailable` می دهد.

---

## لایه cache

تابع اصلی: `batch_authorize_features`

### چرا cache داریم؟

برای جلوگیری از درخواست تکراری به OPA در routeهای پرترافیک.

### کلید cache چگونه ساخته می شود؟

تابع `_get_authorization_cache_key` این داده ها را hash می کند:

- `farm_uuid`
- `user_id`
- `features` به صورت sorted
- `action`
- `route`

سپس خروجی SHA-256 با prefix زیر ذخیره می شود:

- `access-control:authz:<sha256>`

### زمان انقضا

از `ACCESS_CONTROL_AUTHZ_CACHE_TIMEOUT` می آید که پیش فرض آن 300 ثانیه است.

### رفتار خطا در cache

اگر خواندن یا نوشتن cache fail شود:

- خطا swallow می شود
- warning و metric observability ثبت می شود
- authorization ادامه پیدا می کند

پس cache optimization است، نه dependency حیاتی.

---

## نگاشت method به action

تابع `get_authorization_action` از `ACTION_MAP` استفاده می کند:

- `GET`, `HEAD`, `OPTIONS` -> `view`
- `POST` -> `create`
- `PUT`, `PATCH` -> `edit`
- `DELETE` -> `delete`

این action در payload ارسالی به OPA قرار می گیرد.

---

## کنترل دسترسی در سطح Route

پیاده سازی در `access_control/middleware.py`

کلاس: `RouteFeatureAccessMiddleware`

### هدف

قبل از رسیدن request به view، بر اساس app مربوط به route، یک `feature_code` سراسری پیدا کند و اجازه دسترسی را چک کند.

### منبع feature_code برای route

از فایل `config/feature.json` استفاده می شود.

مثلا:

- `account` -> `account_management`
- `farm_hub` -> `farm_management`
- `dashboard` -> `farm_dashboard`
- `notifications` -> `notifications`

### جریان اجرا

1. اگر `view_class` وجود نداشته باشد، middleware کاری نمی کند.
2. اگر view، `AllowAny` داشته باشد، middleware عبور می دهد.
3. اگر user هنوز authenticate نشده باشد، با JWT تلاش به authenticate می کند.
4. از روی نام app در ماژول view، `feature_code` route پیدا می شود.
5. اگر mapping وجود نداشته باشد، request بدون این check عبور می کند.
6. اگر `farm_uuid` در path/query/body باشد، مزرعه متعلق به user لود می شود.
7. تابع `authorize_feature` با context فعلی صدا زده می شود.
8. اگر deny شود، پاسخ `403` برمی گرداند.
9. اگر OPA unavailable باشد، پاسخ `503` برمی گرداند.
10. اگر مجاز باشد، مقدار `request.route_feature_code` ست می شود.

### استخراج farm_uuid

middleware به این ترتیب `farm_uuid` را پیدا می کند:

- `view_kwargs`
- `request.GET`
- `get_request_data(request)` برای body JSON

### نکته مهم

در route-level check، اگر route به مزرعه خاصی وابسته نباشد، `farm=None` به OPA فرستاده می شود. بنابراین policy باید بتواند هر دو حالت farm-aware و farm-less را مدیریت کند.

---

## کنترل دسترسی در سطح View/Feature

پیاده سازی در `access_control/permissions.py`

کلاس: `FeatureAccessPermission`

### هدف

برای viewهایی که یک feature خاص لازم دارند، علاوه بر route-level feature، یک feature جزئی تر هم بررسی شود.

### نحوه فعال شدن

هر view می تواند property زیر را تعریف کند:

```python
required_feature_code = "some_feature_code"
```

اگر این property وجود نداشته باشد، این permission به صورت خودکار `True` برمی گرداند.

### جریان اجرا

1. `required_feature_code` از view خوانده می شود.
2. `farm_uuid` از `kwargs`، `query_params` یا body گرفته می شود.
3. مزرعه با شرط `owner=request.user` لود می شود.
4. `authorize_feature` برای همان feature خاص اجرا می شود.
5. در صورت deny، پیام `Access to feature ... is denied.` تنظیم می شود.
6. در صورت unavailable بودن OPA، متن exception به عنوان message برمی گردد.

### تفاوت با middleware

- middleware بر اساس `app -> route feature` تصمیم می گیرد.
- permission بر اساس `required_feature_code` هر view تصمیم می گیرد.

پس ممکن است یک request از middleware عبور کند، ولی در permission لایه دوم رد شود.

---

## استخراج body برای authorization

تابع `get_request_data` برای این ساخته شده که حتی قبل از parse کامل DRF هم بتوان `farm_uuid` را از request پیدا کرد.

### رفتار

- اگر `request.data` از قبل dict یا `QueryDict` باشد، همان برگردانده می شود.
- اگر body خالی باشد، `{}` برمی گردد.
- اگر `content-type` برابر `application/json` باشد، body parse می شود.
- فقط اگر خروجی یک dict باشد cache می شود و برگردانده می شود.
- اگر parse خطا بدهد، `{}` برمی گردد.

این رفتار مخصوصا برای middleware مهم است، چون آنجا همیشه `request.data` آماده نیست.

---

## API موجود در access_control

در حال حاضر route رسمی app این است:

- `POST /api/access-control/farms/<farm_uuid>/authorize/`

تعریف آن در `access_control/urls.py` آمده است.

### View مربوطه

`FarmFeatureAuthorizationView` در `access_control/views.py`

### ورودی

serializer:

```json
{
  "features": ["farm_dashboard", "notifications"],
  "action": "view"
}
```

- `features` اجباری و non-empty است
- `action` اختیاری است و پیش فرض آن `view` است

### رفتار endpoint

1. کاربر باید authenticate باشد.
2. مزرعه با `farm_uuid` و `owner=request.user` پیدا می شود.
3. request مستقیم به `request_opa_batch_authorization` می رود.
4. پاسخ OPA بدون normalize شدن کامل، داخل `decision` برگردانده می شود.

### پاسخ موفق

ساختار تقریبی:

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "farm_uuid": "...",
    "user": {
      "id": 1,
      "username": "user",
      "email": "user@example.com",
      "phone_number": "0912..."
    },
    "features": ["farm_dashboard"],
    "action": "view",
    "decision": {
      "decisions": {
        "farm_dashboard": true
      }
    }
  }
}
```

### پاسخ های خطا

- `404`: مزرعه پیدا نشد
- `503`: سرویس OPA در دسترس نیست

---

## نگاشت app به feature در `config/feature.json`

این فایل تعیین می کند هر app در سطح route با چه featureی کنترل شود.

نمونه های فعلی:

- `auth` -> `auth_access`
- `account` -> `account_management`
- `farm_hub` -> `farm_management`
- `dashboard` -> `farm_dashboard`
- `irrigation` -> `irrigation`
- `fertilization` -> `fertilization`
- `notifications` -> `notifications`
- `access_control` -> `access_control`

### نکته طراحی

این mapping coarse-grained است؛ یعنی در سطح app عمل می کند، نه در سطح تک endpoint. اگر نیاز به granularity بیشتر باشد، باید یا:

- routeها app-level جدا شوند
- یا روی viewها `required_feature_code` های ریزتر تعریف شود

---

## تعامل با authentication

- authentication پیش فرض پروژه JWT است.
- middleware اگر `request.user` آماده نباشد، خودش با `JWTAuthentication` تلاش می کند کاربر را از روی token شناسایی کند.
- اگر token نامعتبر باشد، middleware سکوت می کند و authentication را به جریان عادی DRF واگذار می کند.

این طراحی باعث می شود middleware برای کاربر ناشناس تصمیم اشتباه نگیرد و با لایه auth اصلی conflict نداشته باشد.

---

## رفتار با viewهای AllowAny

در middleware، اگر view داخل `permission_classes` از `AllowAny` استفاده کند، route-level access control روی آن route اعمال نمی شود.

این رفتار برای endpointهای عمومی مثل login، register، یا webhookها لازم است.

---

## observability و metrics

در `access_control/services.py` چند جای مهم instrumentation وجود دارد:

- `observe_operation(...)` برای اندازه گیری عملیات batch authorization
- `log_event(...)` برای ثبت خطاها و warningها
- `record_metric(...)` برای شمارنده هایی مثل:
  - `access_control.opa.failure`
  - `access_control.opa.invalid_json`
  - `access_control.opa.empty_result`

این داده ها برای monitoring کیفیت ارتباط با OPA مهم هستند.

---

## تست های موجود

تست های اصلی در `access_control/tests.py` و بخشی در `farm_hub/tests.py` قرار دارند.

مواردی که الان تست شده اند:

- cache شدن authorization برای route یکسان
- وجود `route` در payload ارسالی به OPA
- پشتیبانی از payload nested در `normalize_opa_batch_result`
- ثبت metric هنگام invalid JSON از OPA
- ارسال `feature_code` و `action` درست از middleware
- resolve شدن profile بر اساس چند rule مختلف
- fallback شدن subscription plan به پلن پیش فرض

این تست ها نشان می دهند که سیستم هم لایه runtime authorization و هم لایه profile resolution را پوشش داده است.

---

## محدودیت ها و نکات مهم فعلی

### 1) route-level mapping در سطح app است

اگر یک app چند endpoint با سطح دسترسی متفاوت داشته باشد، `config/feature.json` به تنهایی کافی نیست و باید از `required_feature_code` یا سیاست های دقیق تر استفاده شود.

### 2) نقش کاربر فعلا ساده است

در `build_opa_user` مقدار `role` فعلا همیشه `farmer` است. اگر در آینده نقش هایی مثل admin، agronomist یا support اضافه شوند، این بخش باید واقعی تر شود.

### 3) profile builder و runtime OPA دو مسیر متفاوت دارند

- `build_farm_access_profile` ruleها را داخل خود Django resolve می کند.
- runtime authorization از OPA جواب می گیرد.

اگر policyهای OPA و داده های rule داخل Django از هم فاصله بگیرند، ممکن است اختلاف رفتار ایجاد شود. بنابراین باید policyها و rule modelها هماهنگ نگه داشته شوند.

### 4) endpoint رسمی profile در app دیده نمی شود

در کد فعلی `access_control/urls.py` فقط endpoint `authorize` ثبت شده است. پس اگر قرار باشد profile نهایی برای فرانت نمایش داده شود، یا باید endpoint جدید ساخته شود یا از سرویس `build_farm_access_profile` در view دیگری استفاده شود.

### 5) migrationهای seed فعلا خالی هستند

فایل های `0003_seed_default_access_rules.py` و `0004_enable_default_feature_access.py` در وضعیت فعلی عملیات migration ندارند. یعنی seed اولیه ruleها و featureها احتمالا هنوز به صورت migration-based پیاده نشده یا بعدا منتقل شده است.

---

## سناریوی کامل اجرای یک request

فرض کنیم کاربر درخواست زیر را می زند:

- `PATCH /api/account/profile/`

جریان کلی:

1. request وارد middleware می شود.
2. middleware تشخیص می دهد app این route برابر `account` است.
3. از `config/feature.json`، feature برابر `account_management` پیدا می شود.
4. method برابر `PATCH` است، پس action می شود `edit`.
5. context کاربر و مزرعه احتمالی جمع آوری می شود.
6. درخواست batch به OPA ارسال می شود.
7. اگر `account_management` مجاز باشد، request به DRF می رسد.
8. DRF authentication/permissionهای عادی را هم بررسی می کند.
9. اگر view یک `required_feature_code` اضافی داشته باشد، `FeatureAccessPermission` دوباره access را بررسی می کند.
10. اگر همه چیز مجاز باشد، business logic view اجرا می شود.

---

## راهنمای توسعه و افزودن قابلیت جدید

اگر بخواهید یک feature جدید به سیستم اضافه کنید، این مراحل پیشنهاد می شود:

### افزودن feature جدید

1. یک `AccessFeature` جدید با `code` مناسب بسازید.
2. اگر لازم است route-level باشد، app مربوطه را در `config/feature.json` map کنید.
3. اگر granular است، روی view مقدار `required_feature_code` تعریف کنید.
4. policy متناظر را در OPA اضافه یا به روز کنید.
5. اگر profile-based resolution هم مهم است، ruleهای Django را هم اضافه کنید.
6. تست middleware/permission/profile را اضافه کنید.

### افزودن rule جدید

1. `AccessRule` بسازید.
2. featureها را به آن وصل کنید.
3. شرط ها را با یکی یا چند مورد از این ها تنظیم کنید:
   - subscription plan
   - farm type
   - product
   - sensor catalog
   - metadata مثل `sensor_catalog_codes`
4. `priority` را دقیق انتخاب کنید تا overrideها قابل پیش بینی باشند.

---

## جمع بندی

سیستم `access_control` در این پروژه یک لایه دسترسی چندبعدی است که:

- بر پایه user و farm تصمیم می گیرد
- پلن اشتراک، نوع مزرعه، محصول و سنسور را وارد تصمیم می کند
- در سطح route و feature قابل اعمال است
- تصمیم runtime را به OPA واگذار می کند
- برای performance از cache استفاده می کند
- برای profile/resolution داخلی، snapshot قابل ذخیره می سازد

اگر بخواهیم خیلی خلاصه بگوییم:

- `models.py` تعریف می کند چه چیزهایی روی access اثر دارند
- `services.py` context را می سازد، OPA را صدا می زند و نتیجه را normalize می کند
- `middleware.py` روی routeها gatekeeper است
- `permissions.py` روی featureهای ریزتر gatekeeper است
- `feature.json` mapping سطح app را مشخص می کند
- `settings.py` کل سیستم را فعال و تنظیم می کند

