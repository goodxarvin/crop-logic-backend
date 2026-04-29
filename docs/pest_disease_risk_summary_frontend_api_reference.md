# Pest Disease Risk Summary API Reference

این فایل برای فرانت آماده شده تا ساختار خروجی endpoint زیر مشخص و قابل استفاده باشد:

```http
POST /api/pest-disease/risk-summary/
```

## Purpose

این endpoint فقط `farm_uuid` می‌گیرد و در backend:

- مزرعه را پیدا می‌کند
- اولین محصول ثبت‌شده روی همان مزرعه را برمی‌دارد
- `plant_name` را از همان محصول پر می‌کند
- `growth_stage` را فعلاً به صورت ثابت `گلدهی` به سرویس AI می‌فرستد
- خروجی خلاصه ریسک آفت و بیماری را به فرانت برمی‌گرداند

---

## Request

### Body

```json
{
  "farm_uuid": "11111111-1111-1111-1111-111111111111"
}
```

### Request Fields

| field | type | required | description |
|---|---|---:|---|
| `farm_uuid` | `string (uuid)` | yes | UUID مزرعه |

### Important Notes

- این endpoint فقط `farm_uuid` را از کلاینت قبول می‌کند.
- `plant_name` نباید از فرانت ارسال شود.
- `growth_stage` نباید از فرانت ارسال شود.
- `plant_name` در backend از اولین محصول مزرعه استخراج می‌شود.
- اگر مزرعه هیچ محصولی نداشته باشد، `plant_name` به صورت رشته خالی به AI ارسال می‌شود.
- `growth_stage` فعلاً همیشه `گلدهی` است.

---

## Success Response

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "farm_uuid": "11111111-1111-1111-1111-111111111111",
    "diseaseRisk": {
      "id": "disease-risk",
      "title": "ریسک بیماری",
      "subtitle": "فشار بیماری در حال افزایش است",
      "stats": "68%",
      "avatarColor": "warning",
      "avatarIcon": "tabler-biohazard",
      "chipText": "متوسط",
      "chipColor": "warning",
      "details": {
        "reason": "رطوبت بالا و تهویه ضعیف"
      }
    },
    "pestRisk": {
      "id": "pest-risk",
      "title": "ریسک آفت",
      "subtitle": "فعالیت آفات قابل توجه است",
      "stats": "41%",
      "avatarColor": "info",
      "avatarIcon": "tabler-bug",
      "chipText": "کم",
      "chipColor": "success",
      "details": {
        "reason": "شرایط محیطی نسبتاً پایدار"
      }
    },
    "drivers": {
      "humidity": "high",
      "temperature": "moderate"
    }
  }
}
```

---

## Success Response Fields

### Top Level

| field | type | description |
|---|---|---|
| `code` | `number` | در حالت موفق مقدار `200` |
| `msg` | `string` | در حالت موفق مقدار `success` |
| `data` | `object` | محتوای اصلی پاسخ |

### `data`

| field | type | description |
|---|---|---|
| `farm_uuid` | `string` | UUID مزرعه |
| `diseaseRisk` | `object` | کارت ریسک بیماری |
| `pestRisk` | `object` | کارت ریسک آفت |
| `drivers` | `object` | عوامل موثر روی ریسک |

### `diseaseRisk` / `pestRisk`

هر دو فیلد `diseaseRisk` و `pestRisk` یک ساختار مشابه دارند:

| field | type | description |
|---|---|---|
| `id` | `string` | شناسه کارت |
| `title` | `string` | عنوان کارت |
| `subtitle` | `string` | توضیح کوتاه |
| `stats` | `string` | عدد یا درصد اصلی برای نمایش |
| `avatarColor` | `string` | رنگ آیکن یا کارت |
| `avatarIcon` | `string` | نام آیکن |
| `chipText` | `string` | وضعیت متنی مثل `کم`، `متوسط`، `زیاد` |
| `chipColor` | `string` | رنگ وضعیت مثل `success`، `warning`، `error` |
| `details` | `object` | اطلاعات تکمیلی برای UI جزئی‌تر |

### `drivers`

| field | type | description |
|---|---|---|
| `drivers` | `object` | object آزاد از عوامل مؤثر مثل رطوبت، دما، باد، بارندگی و غیره |

نکته:
- ساختار داخلی `drivers` ثابت و محدود نیست و بهتر است در فرانت به صورت dynamic render شود.

---

## Error Response - Missing `farm_uuid`

```json
{
  "code": 400,
  "msg": "error",
  "data": {
    "farm_uuid": ["This field is required."]
  }
}
```

### When Happens

- وقتی `farm_uuid` در body ارسال نشده باشد

---

## Error Response - Farm Not Found

```json
{
  "code": 404,
  "msg": "error",
  "data": {
    "farm_uuid": ["Farm not found."]
  }
}
```

### When Happens

- وقتی `farm_uuid` معتبر باشد ولی مزرعه‌ای با آن پیدا نشود
- یا مزرعه متعلق به کاربر فعلی نباشد

---

## Error Response - Upstream / AI Error

اگر سرویس AI خطا برگرداند، backend همان status code را با این ساختار پاس می‌دهد:

```json
{
  "code": 500,
  "msg": "error",
  "data": {
    "message": "Upstream service error"
  }
}
```

نکته:
- محتویات `data` در این حالت بسته به پاسخ upstream ممکن است متفاوت باشد.

---

## Frontend Notes

- فرم درخواست فقط باید `farm_uuid` بفرستد.
- `diseaseRisk` و `pestRisk` را مثل card model در UI مصرف کنید.
- `drivers` را optional و dynamic در نظر بگیرید.
- اگر یکی از `diseaseRisk` یا `pestRisk` خالی بود، UI باید بدون crash کار کند.
- متن خطا برای `400` و `404` را می‌توانید از `data.farm_uuid[0]` بخوانید.

---

## Suggested TypeScript Interfaces

```ts
export interface RiskCard {
  id?: string;
  title?: string;
  subtitle?: string;
  stats?: string;
  avatarColor?: string;
  avatarIcon?: string;
  chipText?: string;
  chipColor?: string;
  details?: Record<string, unknown>;
}

export interface PestDiseaseRiskSummaryResponse {
  code: number;
  msg: string;
  data: {
    farm_uuid: string;
    diseaseRisk?: RiskCard;
    pestRisk?: RiskCard;
    drivers?: Record<string, unknown>;
  };
}
```

---

## Example Frontend Handling

```ts
const response = await api.post('/api/pest-disease/risk-summary/', {
  farm_uuid,
});

const result = response.data;

if (result.code === 200) {
  const diseaseRisk = result.data.diseaseRisk;
  const pestRisk = result.data.pestRisk;
  const drivers = result.data.drivers;
}
```
