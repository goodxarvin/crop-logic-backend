# Free-Text Plan Parser APIs

این فایل برای تیم فرانت‌اند آماده شده و دو API جدید زیر را توضیح می‌دهد:

- `POST /api/irrigation/plan-from-text/`
- `POST /api/fertilization/plan-from-text/`

هدف هر دو API:

- کاربر یک متن آزاد می‌نویسد
- backend تلاش می‌کند برنامه آبیاری یا کودهی را به JSON ساختاریافته تبدیل کند
- اگر اطلاعات کامل باشد، JSON نهایی برمی‌گردد
- اگر اطلاعات ناقص باشد، API سوال‌های تکمیلی برمی‌گرداند
- فرانت‌اند سوال‌ها را از کاربر می‌پرسد و پاسخ‌ها را دوباره برای API می‌فرستد

---

## رفتار کلی هر دو API

هر دو endpoint یک flow یکسان دارند:

1. کاربر متن آزاد اولیه را می‌فرستد
2. اگر متن کامل باشد:
   - `status = "completed"`
   - `final_plan` برمی‌گردد
3. اگر متن ناقص باشد:
   - `status = "needs_clarification"`
   - `missing_fields` برمی‌گردد
   - `questions` برمی‌گردد
4. فرانت‌اند پاسخ کاربر به سوال‌ها را جمع می‌کند
5. دوباره همان endpoint را با `answers` و `partial_plan` صدا می‌زند
6. این روند تا ساخته شدن `final_plan` ادامه پیدا می‌کند

---

## الگوی کلی response

هر دو API از envelope استاندارد استفاده می‌کنند:

```json
{
  "code": 200,
  "msg": "موفق",
  "data": {}
}
```

### معنی فیلدهای envelope

| فیلد | نوع | توضیح |
|---|---|---|
| `code` | number | کد منطقی پاسخ |
| `msg` | string | پیام کوتاه پاسخ |
| `data` | object | داده اصلی API |

---

## 1) API استخراج برنامه آبیاری

### Endpoint

```http
POST /api/irrigation/plan-from-text/
```

### کاربرد

این API متن آزاد کاربر درباره برنامه آبیاری را به JSON ساختاریافته تبدیل می‌کند.

### Request Body

هر سه فیلد زیر اختیاری هستند، اما حداقل یکی از این‌ها باید ارسال شود:

- `message`
- `answers`
- `partial_plan`

#### ساختار request

```json
{
  "message": "برای گوجه فرنگی با آبیاری قطره ای هر سه روز یک بار صبح زود 25 دقیقه آبیاری می کنم و حدود 18 لیتر برای هر بوته می دهم.",
  "answers": {
    "growth_stage": "گلدهی"
  },
  "partial_plan": {
    "crop_name": "گوجه فرنگی",
    "irrigation_method": "قطره ای"
  },
  "farm_uuid": "11111111-1111-1111-1111-111111111111"
}
```

### فیلدهای request

| فیلد | نوع | اجباری | توضیح |
|---|---|---:|---|
| `message` | string | خیر | متن آزاد کاربر |
| `answers` | object | خیر | پاسخ‌های تکمیلی کاربر به سوال‌هایی که قبلا API داده |
| `partial_plan` | object | خیر | خروجی مرحله قبل برای ادامه تکمیل |
| `farm_uuid` | string | خیر | برای غنی‌سازی context مزرعه در AI |

### قانون validation

اگر هیچ‌کدام از `message`، `answers` یا `partial_plan` ارسال نشوند:

```json
{
  "code": 400,
  "msg": "Bad Request",
  "data": {
    "non_field_errors": [
      "حداقل یکی از message، answers یا partial_plan باید ارسال شود."
    ]
  }
}
```

---

## پاسخ موفق - حالت تکمیل شده

وقتی همه اطلاعات لازم موجود باشد:

```json
{
  "code": 200,
  "msg": "موفق",
  "data": {
    "status": "completed",
    "status_fa": "تکمیل شد",
    "summary": "برنامه آبیاری برای گوجه‌فرنگی به روش قطره‌ای هر سه روز یک‌بار صبح زود به مدت 25 دقیقه اجرا می‌شود.",
    "missing_fields": [],
    "questions": [],
    "collected_data": {
      "crop_name": "گوجه‌فرنگی",
      "growth_stage": "گلدهی",
      "irrigation_method": "قطره‌ای",
      "water_amount_per_event": "18 لیتر برای هر بوته",
      "duration_minutes": 25,
      "frequency_text": "هر سه روز یک‌بار",
      "interval_days": 3,
      "preferred_time_of_day": "صبح زود",
      "start_date": "از امروز",
      "target_area": "کل مزرعه",
      "trigger_conditions": [],
      "notes": []
    },
    "final_plan": {
      "crop_name": "گوجه‌فرنگی",
      "growth_stage": "گلدهی",
      "irrigation_method": "قطره‌ای",
      "water_amount_per_event": "18 لیتر برای هر بوته",
      "duration_minutes": 25,
      "frequency_text": "هر سه روز یک‌بار",
      "interval_days": 3,
      "preferred_time_of_day": "صبح زود",
      "start_date": "از امروز",
      "target_area": "کل مزرعه",
      "trigger_conditions": [],
      "notes": []
    }
  }
}
```

### فیلدهای `data`

| فیلد | نوع | توضیح |
|---|---|---|
| `status` | string | یکی از `completed` یا `needs_clarification` |
| `status_fa` | string | نسخه فارسی وضعیت |
| `summary` | string | خلاصه قابل نمایش برای کاربر |
| `missing_fields` | array[string] | فیلدهای ناقص |
| `questions` | array[object] | سوال‌های تکمیلی |
| `collected_data` | object | داده‌ای که تا الان از متن و جواب‌ها استخراج شده |
| `final_plan` | object/null | برنامه نهایی؛ فقط در حالت `completed` |

### فیلدهای `collected_data` و `final_plan`

| فیلد | نوع | توضیح |
|---|---|---|
| `crop_name` | string | نام محصول |
| `growth_stage` | string | مرحله رشد محصول |
| `irrigation_method` | string | روش آبیاری |
| `water_amount_per_event` | string | مقدار آب هر نوبت |
| `duration_minutes` | number | مدت هر نوبت آبیاری به دقیقه |
| `frequency_text` | string | توصیف متنی فاصله آبیاری |
| `interval_days` | number | فاصله آبیاری بر حسب روز |
| `preferred_time_of_day` | string | زمان مناسب اجرای آبیاری |
| `start_date` | string | زمان یا تاریخ شروع برنامه |
| `target_area` | string | محدوده هدف برنامه |
| `trigger_conditions` | array[string] | شرایط تریگر اختیاری |
| `notes` | array[string] | نکات تکمیلی |

---

## پاسخ موفق - حالت نیاز به سوال تکمیلی

اگر اطلاعات کامل نباشد:

```json
{
  "code": 200,
  "msg": "موفق",
  "data": {
    "status": "needs_clarification",
    "status_fa": "نیازمند پرسش تکمیلی",
    "summary": "اطلاعات برنامه آبیاری برای ساخت JSON نهایی کافی نیست و به چند پاسخ تکمیلی نیاز است.",
    "missing_fields": [
      "growth_stage",
      "start_date",
      "target_area"
    ],
    "questions": [
      {
        "id": "growth_stage",
        "field": "growth_stage",
        "question": "محصول الان در چه مرحله رشدی قرار دارد؟",
        "rationale": "مرحله رشد برای کامل شدن برنامه لازم است."
      },
      {
        "id": "start_date",
        "field": "start_date",
        "question": "این برنامه از چه تاریخی یا از چه زمانی باید شروع شود؟",
        "rationale": "زمان شروع برنامه هنوز مشخص نشده است."
      },
      {
        "id": "target_area",
        "field": "target_area",
        "question": "این برنامه برای کل مزرعه است یا بخش/ناحیه خاصی از مزرعه؟",
        "rationale": "محدوده اجرای برنامه باید مشخص باشد."
      }
    ],
    "collected_data": {
      "crop_name": "گوجه‌فرنگی",
      "growth_stage": null,
      "irrigation_method": "قطره‌ای",
      "water_amount_per_event": "18 لیتر برای هر بوته",
      "duration_minutes": 25,
      "frequency_text": "هر سه روز یک‌بار",
      "interval_days": 3,
      "preferred_time_of_day": "صبح زود",
      "start_date": null,
      "target_area": null,
      "trigger_conditions": [],
      "notes": []
    },
    "final_plan": null
  }
}
```

### ساختار `questions`

| فیلد | نوع | توضیح |
|---|---|---|
| `id` | string | شناسه سوال |
| `field` | string | فیلدی که این سوال برای آن پرسیده شده |
| `question` | string | متن سوال برای نمایش به کاربر |
| `rationale` | string | توضیح کوتاه برای اینکه چرا این سوال لازم است |

---

## flow پیشنهادی فرانت‌اند برای آبیاری

### مرحله 1

کاربر متن آزاد می‌فرستد:

```json
{
  "message": "برای گوجه فرنگی هر سه روز یک بار آبیاری می کنم."
}
```

### مرحله 2

اگر `status = needs_clarification` بود:

- سوال‌ها را از `data.questions` به کاربر نمایش بده
- پاسخ‌ها را جمع کن

### مرحله 3

درخواست تکمیلی بزن:

```json
{
  "partial_plan": {
    "crop_name": "گوجه فرنگی",
    "growth_stage": null,
    "irrigation_method": null,
    "water_amount_per_event": null,
    "duration_minutes": null,
    "frequency_text": "هر سه روز یک بار",
    "interval_days": 3,
    "preferred_time_of_day": null,
    "start_date": null,
    "target_area": null,
    "trigger_conditions": [],
    "notes": []
  },
  "answers": {
    "growth_stage": "گلدهی",
    "irrigation_method": "قطره ای",
    "water_amount_per_event": "18 لیتر برای هر بوته",
    "duration_minutes": 25,
    "preferred_time_of_day": "صبح زود",
    "start_date": "از امروز",
    "target_area": "کل مزرعه"
  }
}
```

### مرحله 4

اگر `status = completed` شد:

- از `data.final_plan` به عنوان JSON نهایی استفاده کن

---

## 2) API استخراج برنامه کودهی

### Endpoint

```http
POST /api/fertilization/plan-from-text/
```

### کاربرد

این API متن آزاد کاربر درباره برنامه کودهی را به JSON ساختاریافته تبدیل می‌کند.

### Request Body

```json
{
  "message": "برای گندم در مرحله پنجه زنی هر 12 روز یک بار 20-20-20 به مقدار 35 کیلوگرم در هکتار از طریق کودآبیاری می دهم.",
  "answers": {
    "timing": "هر 12 روز یک بار"
  },
  "partial_plan": {
    "crop_name": "گندم"
  },
  "farm_uuid": "11111111-1111-1111-1111-111111111111"
}
```

### فیلدهای request

| فیلد | نوع | اجباری | توضیح |
|---|---|---:|---|
| `message` | string | خیر | متن آزاد کاربر |
| `answers` | object | خیر | پاسخ‌های تکمیلی کاربر |
| `partial_plan` | object | خیر | داده استخراج شده مرحله قبل |
| `farm_uuid` | string | خیر | برای context مزرعه |

### validation error

```json
{
  "code": 400,
  "msg": "Bad Request",
  "data": {
    "non_field_errors": [
      "حداقل یکی از message، answers یا partial_plan باید ارسال شود."
    ]
  }
}
```

---

## پاسخ موفق - حالت تکمیل شده

```json
{
  "code": 200,
  "msg": "موفق",
  "data": {
    "status": "completed",
    "status_fa": "تکمیل شد",
    "summary": "برنامه کودهی برای گندم در مرحله پنجه زنی با کود 20-20-20 به صورت کودآبیاری هر 12 روز یک بار اجرا می شود.",
    "missing_fields": [],
    "questions": [],
    "collected_data": {
      "crop_name": "گندم",
      "growth_stage": "پنجه زنی",
      "objective": "تقویت رشد رویشی",
      "applications": [
        {
          "fertilizer_name": "کود کامل 20-20-20",
          "formula": "20-20-20",
          "amount": "35 کیلوگرم در هکتار",
          "application_method": "کودآبیاری",
          "timing": "هر 12 روز یک بار",
          "interval_days": 12,
          "purpose": "تقویت رشد رویشی"
        }
      ],
      "notes": []
    },
    "final_plan": {
      "crop_name": "گندم",
      "growth_stage": "پنجه زنی",
      "objective": "تقویت رشد رویشی",
      "applications": [
        {
          "fertilizer_name": "کود کامل 20-20-20",
          "formula": "20-20-20",
          "amount": "35 کیلوگرم در هکتار",
          "application_method": "کودآبیاری",
          "timing": "هر 12 روز یک بار",
          "interval_days": 12,
          "purpose": "تقویت رشد رویشی"
        }
      ],
      "notes": []
    }
  }
}
```

### فیلدهای `collected_data` و `final_plan`

| فیلد | نوع | توضیح |
|---|---|---|
| `crop_name` | string | نام محصول |
| `growth_stage` | string | مرحله رشد |
| `objective` | string/null | هدف برنامه |
| `applications` | array[object] | لیست نوبت‌ها یا اقلام کودی |
| `notes` | array[string] | نکات تکمیلی |

### ساختار هر application

| فیلد | نوع | توضیح |
|---|---|---|
| `fertilizer_name` | string | نام کود |
| `formula` | string | فرمول یا آنالیز کود |
| `amount` | string | مقدار مصرف |
| `application_method` | string | روش مصرف |
| `timing` | string | زمان‌بندی مصرف |
| `interval_days` | number | فاصله بین نوبت‌ها |
| `purpose` | string/null | هدف آن نوبت |

---

## پاسخ موفق - حالت نیاز به سوال تکمیلی

```json
{
  "code": 200,
  "msg": "موفق",
  "data": {
    "status": "needs_clarification",
    "status_fa": "نیازمند پرسش تکمیلی",
    "summary": "اطلاعات برنامه کودهی برای ساخت JSON نهایی کافی نیست و به چند پاسخ تکمیلی نیاز است.",
    "missing_fields": [
      "growth_stage",
      "formula",
      "interval_days"
    ],
    "questions": [
      {
        "id": "growth_stage",
        "field": "growth_stage",
        "question": "محصول الان در چه مرحله رشدی قرار دارد؟",
        "rationale": "مرحله رشد برای تکمیل برنامه لازم است."
      },
      {
        "id": "formula",
        "field": "formula",
        "question": "فرمول یا آنالیز کود چیست؟ مثلا 20-20-20.",
        "rationale": "ترکیب دقیق کود هنوز مشخص نشده است."
      },
      {
        "id": "interval_days",
        "field": "interval_days",
        "question": "فاصله بین نوبت های مصرف کود چند روز است؟",
        "rationale": "عدد فاصله بین نوبت ها برای JSON نهایی لازم است."
      }
    ],
    "collected_data": {
      "crop_name": "گندم",
      "growth_stage": null,
      "objective": null,
      "applications": [
        {
          "fertilizer_name": "کود کامل",
          "formula": null,
          "amount": "35 کیلوگرم در هکتار",
          "application_method": "کودآبیاری",
          "timing": "هر چند وقت یک بار",
          "interval_days": null,
          "purpose": null
        }
      ],
      "notes": []
    },
    "final_plan": null
  }
}
```

---

## flow پیشنهادی فرانت‌اند برای کودهی

### درخواست اولیه

```json
{
  "message": "برای گندم از کود کامل استفاده می کنم."
}
```

### اگر incomplete بود

- از `questions` سوال‌ها را بگیر
- در UI نمایش بده
- پاسخ‌ها را جمع کن

### درخواست تکمیلی

```json
{
  "partial_plan": {
    "crop_name": "گندم",
    "growth_stage": null,
    "objective": null,
    "applications": [
      {
        "fertilizer_name": "کود کامل",
        "formula": null,
        "amount": null,
        "application_method": null,
        "timing": null,
        "interval_days": null,
        "purpose": null
      }
    ],
    "notes": []
  },
  "answers": {
    "growth_stage": "پنجه زنی",
    "formula": "20-20-20",
    "amount": "35 کیلوگرم در هکتار",
    "application_method": "کودآبیاری",
    "timing": "هر 12 روز یک بار",
    "interval_days": 12
  }
}
```

### اگر complete شد

- از `final_plan` استفاده کن

---

## نکات مهم برای فرانت‌اند

### 1. به `status` تکیه کنید

مهم‌ترین فیلد برای کنترل flow:

- `completed`
- `needs_clarification`

### 2. اگر `needs_clarification` بود

باید:

- `questions` را به کاربر نمایش دهید
- `partial_plan` را نگه دارید
- پاسخ‌های کاربر را در `answers` ارسال کنید

### 3. اگر `completed` بود

باید:

- `final_plan` را به عنوان نسخه نهایی برنامه ذخیره یا نمایش دهید

### 4. `collected_data` همیشه مهم است

حتی اگر برنامه ناقص باشد، `collected_data` نشان می‌دهد سیستم تا این لحظه چه چیزهایی را فهمیده است.

### 5. null در حالت ناقص طبیعی است

در حالت `needs_clarification` ممکن است بعضی فیلدهای `collected_data` `null` باشند.
اما در حالت `completed` نباید فیلدهای اصلی ناقص باشند.

### 6. بهتر است سوال‌ها را step-by-step بپرسید

پیشنهاد:

- سوال اول را نشان بده
- جواب را بگیر
- همه جواب‌ها را در `answers` جمع کن
- دوباره API را صدا بزن

---

## جمع‌بندی تفاوت دو API

| API | موضوع | خروجی نهایی |
|---|---|---|
| `/api/irrigation/plan-from-text/` | استخراج برنامه آبیاری | `final_plan` با ساختار آبیاری |
| `/api/fertilization/plan-from-text/` | استخراج برنامه کودهی | `final_plan` با ساختار کودهی |

---

## مسیر فایل

این داکیومنت در این مسیر ذخیره شده:

`docs/irrigation_fertilization_plan_parser_apis.md`
