# گزارش تغییرات API در ۶ کامیت اخیر

این فایل تغییرات مربوط به سه فایل زیر را نسبت به **۶ کامیت قبل** (`HEAD~6`) مستند می‌کند:

- `irrigation/urls.py`
- `fertilization/apps.py`
- `farm_ai_assistant/views.py`

## بازه مقایسه
- مبدا: `HEAD~6`
- مقصد: `HEAD`

## نتیجه سریع
- در `irrigation/urls.py`، API آبیاری از مدل دارای endpoint بررسی وضعیت task فاصله گرفته و دو endpoint جدید برای لیست روش‌های آبیاری و water stress اضافه شده است.
- در `fertilization/apps.py`، در این بازه **هیچ تغییری** ثبت نشده است.
- در `farm_ai_assistant/views.py`، API چت از flow مبتنی بر task/polling به flow مستقیم request/response تغییر کرده و پشتیبانی از `history`، `image_urls` و ورودی‌های multipart/JSON بهتر شده است.

## 1) تغییرات `irrigation/urls.py`

### وضعیت قبلی
مسیرهای زیر وجود داشتند:
- `config/` -> `ConfigView`
- `recommend/` -> `RecommendView`
- `recommend/status/<str:task_id>/` -> `RecommendTaskStatusView`

### وضعیت فعلی
مسیرهای فعلی:
- `` -> `IrrigationMethodListView`
- `config/` -> `ConfigView`
- `recommend/` -> `RecommendView`
- `water-stress/` -> `WaterStressView`

### تغییرات دقیق
#### الف) اضافه شدن endpoint ریشه برای لیست روش‌های آبیاری
مسیر جدید:
- `GET irrigation/`
- view: `IrrigationMethodListView`
- name: `irrigation-method-list`

اثر:
- حالا این app علاوه بر recommendation، یک endpoint مستقل برای دریافت لیست روش‌های آبیاری هم دارد.

#### ب) حذف endpoint بررسی وضعیت task
مسیر حذف‌شده:
- `recommend/status/<str:task_id>/`
- view: `RecommendTaskStatusView`
- name: `irrigation-recommendation-task-status`

اثر:
- دیگر API رسمی‌ای در `urls.py` برای polling وضعیت task recommendation تعریف نشده است.
- این تغییر از نظر معماری شبیه حذف flow تسک‌محور در بخش AI assistant است.

#### ج) اضافه شدن endpoint جدید water stress
مسیر جدید:
- `POST irrigation/water-stress/`
- view: `WaterStressView`
- name: `irrigation-water-stress`

اثر:
- یک قابلیت جدید در API آبیاری اضافه شده که به‌صورت جداگانه water stress را محاسبه/برمی‌گرداند.

### چیزهایی که تغییر نکرده‌اند
- `config/`
- `recommend/`

## 2) تغییرات `fertilization/apps.py`

در بازه `HEAD~6..HEAD` برای این فایل **هیچ diffای وجود ندارد**.

### وضعیت فعلی و قبلی یکسان است
مقدارهای مهم بدون تغییر مانده‌اند:
- `default_auto_field = "django.db.models.BigAutoField"`
- `name = "fertilization"`
- `verbose_name = "Fertilization Recommendation"`

### نتیجه
- از نظر ثبت app در Django، در این ۶ کامیت اخیر تغییری در `fertilization/apps.py` اعمال نشده است.
- اگر منظورت بررسی APIهای recommendation بوده، این فایل خودش route یا view API ندارد و فقط تنظیمات app را نگه می‌دارد.

## 3) تغییرات `farm_ai_assistant/views.py`

بزرگ‌ترین تغییرات این بازه در این فایل اتفاق افتاده است.

### خلاصه معماری
API چت از این مدل:
1. ثبت درخواست چت
2. ساخت task در سرویس AI
3. دریافت `task_id`
4. polling برای status

به این مدل تغییر کرده:
1. ارسال مستقیم درخواست چت
2. دریافت مستقیم پاسخ assistant
3. ذخیره هم‌زمان پیام کاربر و پیام assistant

### تغییرات مهم
#### الف) حذف flow مبتنی بر task
کلاس‌های زیر حذف شده‌اند:
- `ChatTaskCreateView`
- `ChatTaskStatusView`

رفتار قبلی:
- `ChatTaskCreateView` درخواست را به endpoint زیر در سرویس بیرونی می‌فرستاد:
  - `/rag/chat/generate`
- سپس `ChatTaskStatusView` وضعیت task را از endpoint زیر می‌گرفت:
  - `/tasks/{task_id}/status`

رفتار جدید:
- این دو کلاس حذف شده‌اند و flow task-based از این فایل کنار رفته است.

اثر:
- دیگر پاسخ چت در دو مرحله create/status مدیریت نمی‌شود.
- polling مبتنی بر `task_id` از منطق این viewها حذف شده است.

#### ب) مستقیم شدن درخواست چت در `ChatView`
در `ChatView.post`، اکنون درخواست مستقیم به سرویس AI ارسال می‌شود:
- endpoint جدید آداپتر: `/api/rag/chat/`

این یعنی:
- به‌جای submit task و پیگیری وضعیت آن، پاسخ assistant در همان request برگردانده می‌شود.

#### ج) تغییر مدل ورودی از `content` به `query`
در payload ارسالی به adapter، حالا فیلد اصلی متن کاربر این است:
- `query`

در نسخه قبلی، از `content` برای ساخت payload استفاده می‌شد.
الان:
- `content` در منطق اصلی جای خود را به `query` داده است.

اثر:
- کلاینتی که هنوز payload قدیمی مبتنی بر `content` می‌فرستد، باید با قرارداد جدید view/serializer هماهنگ شود.

#### د) پشتیبانی از `history`
قابلیت جدید:
- history پیام‌ها به‌صورت ساختاریافته دریافت، نرمال‌سازی و به adapter ارسال می‌شود.

تغییرات مرتبط:
- اضافه شدن `_serialize_history_messages`
- اضافه شدن `_merge_history`
- اضافه شدن `history` به payload ارسالی به سرویس بیرونی

اثر:
- API حالا می‌تواند context مکالمه را شفاف‌تر و مستقل از صرفاً conversation id به سرویس AI بفرستد.
- اگر history در ورودی باشد، استفاده می‌شود؛ در غیر این صورت از پیام‌های conversation برای ساخت history استفاده می‌شود.

#### ه) پشتیبانی از `image_urls` و فایل آپلودی
قابلیت‌های جدید:
- `image_urls` به payload اضافه شده است.
- فایل‌های آپلودشده نیز جمع‌آوری و به payload الصاق می‌شوند.

تغییرات مرتبط:
- اضافه شدن `_attach_uploaded_files`
- تبدیل `history` و `image_urls` به JSON string هنگام multipart submission
- ادغام `image_urls` و `images` در ذخیره پیام کاربر

اثر:
- API چت حالا هم لینک تصویر و هم فایل تصویر آپلودی را پشتیبانی می‌کند.
- درخواست‌های multipart برای سناریوهای image-based chat بهتر پشتیبانی می‌شوند.

#### و) مدیریت بهتر JSON و خطای Parse
قابلیت‌های جدید:
- import شدن `ParseError`
- اضافه شدن `_parse_json_array`
- اضافه شدن `_prepare_chat_input`
- پاسخ ۴۰۰ اختصاصی برای JSON نامعتبر

رفتار جدید:
- اگر body نامعتبر باشد، API این پیام را برمی‌گرداند:
  - invalid JSON / extra trailing characters
- فیلدهایی مثل `history` و `image_urls` اگر به شکل string JSON بیایند، parse می‌شوند.

اثر:
- endpoint چت در برابر فرمت‌های مختلف درخواست مقاوم‌تر شده است.
- احتمال خطا برای کلاینت‌هایی که multipart یا JSON string می‌فرستند کمتر شده است.

#### ز) تغییر در ساخت conversation جدید
رفتار جدید:
- عنوان conversation با `_generate_conversation_title(query)` ساخته می‌شود.
- اگر query خالی باشد، عنوان پیش‌فرض `Image` می‌شود.
- برای conversation جدید، `farm_context` به‌صورت خالی `{}` ست می‌شود.

رفتار حذف‌شده:
- دیگر `farm_context` و `title` مستقیماً از payload برای update/create conversation استفاده نمی‌شوند.
- منطق قبلی که conversation موجود را با `farm_context` یا `title` آپدیت می‌کرد حذف شده است.

اثر:
- کنترل عنوان مکالمه بیشتر به منطق داخلی view منتقل شده است.
- payload کلاینت اختیار کمتری روی title/farm_context conversation دارد.

#### ح) بهبود نرمال‌سازی پاسخ assistant
در نرمال‌سازی sectionها، این کلیدها هم پشتیبانی می‌شوند:
- `primaryAction`
- `validityPeriod`

اثر:
- ساختار response assistant برای UIهای غنی‌تر آماده‌تر شده است.

#### ط) حذف وابستگی به mock chat response
حذف شده:
- `CHAT_RESPONSE_DATA`
- متد `_build_mock_assistant_payload`

اثر:
- منطق چت بیشتر به پاسخ واقعی adapter متکی شده و از mock response داخلی فاصله گرفته است.

#### ی) logging بیشتر برای دیباگ integration
موارد جدید:
- import شدن `logging`
- تعریف `logger`
- ثبت log برای response adapter و برخی وضعیت‌های payload parsing/extraction

اثر:
- عیب‌یابی integration با سرویس AI ساده‌تر شده است.

## جمع‌بندی نهایی
در این ۶ کامیت اخیر:

- `irrigation/urls.py`
  - endpoint بررسی وضعیت task حذف شده
  - endpoint ریشه برای لیست روش‌های آبیاری اضافه شده
  - endpoint جدید `water-stress/` اضافه شده

- `fertilization/apps.py`
  - هیچ تغییری نداشته است

- `farm_ai_assistant/views.py`
  - flow چت task-based حذف شده
  - درخواست مستقیم به `/api/rag/chat/` جایگزین شده
  - پشتیبانی از `history`، `image_urls` و فایل آپلودی اضافه شده
  - مدیریت JSON/multipart بهتر شده
  - title conversation از `query` ساخته می‌شود
  - نرمال‌سازی response assistant گسترش یافته است
