# Yield/Harvest Prediction API Changes

این فایل تغییرات 3 API زیر را توضیح می‌دهد:

- `POST /api/yield-harvest/harvest-prediction/`
- `POST /api/yield-harvest/yield-prediction/`
- `POST /api/yield-harvest/current-farm-chart/`

---

## خلاصه تغییرات

تغییر اصلی در هر 3 endpoint این است که backend حالا context موردنیاز AI را خودش از روی مزرعه و planهای انتخابی می‌سازد.

### قبل

در استفاده قدیمی، معمولاً فرض می‌شد client باید context بیشتری برای AI بفرستد.

### الآن

- `farm_uuid` ورودی اصلی و الزامی است.
- `plant_name` اگر هم توسط client ارسال شود، مبنای نهایی backend نیست و از روی مزرعه بازنویسی/resolve می‌شود.
- در صورت نیاز، `irrigation_plan_id` و `fertilization_plan_id` هم می‌توانند ارسال شوند.
- اگر plan انتخابی معتبر و متعلق به همان مزرعه کاربر باشد، backend محتوای آن را به payload ارسالی به AI اضافه می‌کند.
- خروجی backend به‌صورت یکدست با فرمت `code / msg / data` برگردانده می‌شود.

---

## Request Contract جدید

هر 3 API از این قرارداد ورودی استفاده می‌کنند:

```json
{
  "farm_uuid": "11111111-1111-1111-1111-111111111111",
  "irrigation_plan_id": 12,
  "fertilization_plan_id": 34
}
```

### فیلدها

- `farm_uuid` اجباری
- `irrigation_plan_id` اختیاری
- `fertilization_plan_id` اختیاری

### نکته مهم

اگر client `plant_name` بفرستد، در این APIها مبنای نهایی backend نیست؛ backend نام گیاه را از مزرعه استخراج می‌کند.

---

## 1) POST `/api/yield-harvest/current-farm-chart/`

### تغییرات

- ورودی endpoint عملاً بر پایه `farm_uuid` کار می‌کند و `plant_name` از context مزرعه تعیین می‌شود.
- backend به‌صورت خودکار `plant_name` را از مزرعه پیدا می‌کند.
- در صورت ارسال `irrigation_plan_id`، اطلاعات برنامه آبیاری داخل payload ارسالی به AI قرار می‌گیرد.
- در صورت ارسال `fertilization_plan_id`، اطلاعات برنامه کودی هم اضافه می‌شود.

### نمونه request

```json
{
  "farm_uuid": "11111111-1111-1111-1111-111111111111"
}
```

### payload ارسالی backend به AI

نمونه مفهومی:

```json
{
  "farm_uuid": "11111111-1111-1111-1111-111111111111",
  "plant_name": "گوجه‌فرنگی"
}
```

### در صورت انتخاب plan

نمونه مفهومی:

```json
{
  "farm_uuid": "11111111-1111-1111-1111-111111111111",
  "plant_name": "گوجه‌فرنگی",
  "irrigation_plan": {
    "id": 12,
    "plan_payload": {
      "plan": {
        "durationMinutes": 20
      }
    }
  }
}
```

### پاسخ موفق

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "farm_uuid": "11111111-1111-1111-1111-111111111111",
    "plant_name": "گوجه‌فرنگی",
    "scenario_id": 1,
    "categories": ["day1"],
    "series": {
      "biomass": [1.2]
    }
  }
}
```

---

## 2) POST `/api/yield-harvest/harvest-prediction/`

### تغییرات

- ورودی endpoint عملاً بر پایه `farm_uuid` کار می‌کند و `plant_name` توسط backend تعیین می‌شود.
- امکان ارسال `fertilization_plan_id` و `irrigation_plan_id` برای enrich کردن context اضافه/پشتیبانی شده است.
- پاسخ AI بعد از extract شدن در `data.result`، به شکل مستقیم در `data` برگردانده می‌شود.

### نمونه request

```json
{
  "farm_uuid": "11111111-1111-1111-1111-111111111111",
  "fertilization_plan_id": 34
}
```

### payload ارسالی backend به AI

```json
{
  "farm_uuid": "11111111-1111-1111-1111-111111111111",
  "plant_name": "گوجه‌فرنگی",
  "fertilization_plan": {
    "id": 34,
    "plan_payload": {
      "primary_recommendation": {
        "fertilizer_code": "npk-151515"
      }
    }
  }
}
```

### پاسخ موفق

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "date": "2026-07-15",
    "dateFormatted": "15 Jul 2026",
    "daysUntil": 96,
    "gddDetails": {
      "current": 800
    }
  }
}
```

---

## 3) POST `/api/yield-harvest/yield-prediction/`

### تغییرات

- مثل دو endpoint دیگر، `plant_name` از روی مزرعه resolve می‌شود.
- در نبود محصول مستقیم روی مزرعه، backend از fallback مناسب مزرعه استفاده می‌کند.
- امکان ارسال `irrigation_plan_id` و `fertilization_plan_id` برای فرستادن context planها به AI اضافه/پشتیبانی شده است.
- پاسخ نهایی با ساختار یکنواخت `code / msg / data` برگردانده می‌شود.

### نمونه request

```json
{
  "farm_uuid": "11111111-1111-1111-1111-111111111111",
  "irrigation_plan_id": 12,
  "fertilization_plan_id": 34
}
```

### payload ارسالی backend به AI

```json
{
  "farm_uuid": "11111111-1111-1111-1111-111111111111",
  "plant_name": "گوجه‌فرنگی",
  "irrigation_plan": {
    "id": 12,
    "plan_payload": {
      "plan": {
        "durationMinutes": 30
      }
    }
  },
  "fertilization_plan": {
    "id": 34,
    "plan_payload": {
      "primary_recommendation": {
        "fertilizer_code": "npk-202020"
      }
    }
  }
}
```

### پاسخ موفق

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "farm_uuid": "11111111-1111-1111-1111-111111111111",
    "predictedYieldTons": 8.4,
    "scenarioId": 1
  }
}
```

---

## خطاها و Validation

### 1) مزرعه نامعتبر یا متعلق به کاربر دیگر

در این حالت endpoint خطای دسترسی/یافت‌نشدن مزرعه برمی‌گرداند.

### 2) plan نامعتبر یا متعلق به مزرعه دیگر

اگر `irrigation_plan_id` یا `fertilization_plan_id` متعلق به همان مزرعه کاربر نباشد، درخواست با خطا رد می‌شود.

نمونه:

```json
{
  "code": 404,
  "msg": "error",
  "data": {
    "irrigation_plan_id": [
      "Irrigation plan not found."
    ]
  }
}
```

### 3) خطای validation ورودی

اگر `farm_uuid` ارسال نشود یا `plan_id`ها نامعتبر باشند، serializer خطای validation برمی‌گرداند.

---

## جمع‌بندی تغییرات برای فرانت

- دیگر لازم نیست `plant_name` را برای این 3 API بفرستید.
- فقط `farm_uuid` اجباری است.
- اگر کاربر plan خاصی را انتخاب کرده، `irrigation_plan_id` و/یا `fertilization_plan_id` را هم بفرستید.
- response هر 3 endpoint با ساختار یکنواخت `code`, `msg`, `data` برمی‌گردد.
- backend خودش payload مناسب AI را از context مزرعه و planهای انتخابی می‌سازد.
