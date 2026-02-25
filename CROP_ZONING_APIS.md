# مستندات APIهای زون‌بندی کشت (Crop Zoning)

این سند تمام APIهای مورد نیاز برای صفحه **Crop Zoning** را شرح می‌دهد: ورودی‌ها، خروجی‌ها، محصولات، رنگ‌ها، مساحت کلی و دیتای هر بخش زمین به صورت جداگانه.

**مسیر صفحه:** `(dashboard)/(private)/crop-zoning`  
**کامپوننت اصلی:** `CropZoningWrapper`

---

## نمای کلی و جریان درخواست‌ها

```
۱. GET area                    → منطقهٔ ثابت (کاربر امکان رسم ندارد)
۲. GET products                → لیست محصولات و رنگ‌ها
۳. POST zones/initial          → ارسال محدودهٔ مربع‌ها → دیتای محصولات پیشنهادی (نقشه + tooltip)
۴. POST zones/water-need       → ارسال محدودهٔ مربع‌ها → نیاز آبی هر منطقه
۵. POST zones/soil-quality     → ارسال محدودهٔ مربع‌ها → کیفیت خاک هر منطقه
۶. POST zones/cultivation-risk → ارسال محدودهٔ مربع‌ها → ریسک کشت هر منطقه
۷. GET zone/:zoneId            → کلیک روی مربع → دیتای تکمیلی (پنل جزئیات: reason, criteria, ...)
```

| ردیف | API | هدف |
|------|-----|------|
| ۱ | **منطقهٔ اولیه** | دریافت منطقهٔ زمین به صورت GeoJSON؛ کاربر نمی‌تواند چیزی رسم کند |
| ۲ | **لیست محصولات و رنگ‌ها** | دریافت محصولات قابل کشت به همراه رنگ نمایش و لیبل فارسی |
| ۳ | **دیتای اولیه زون‌ها (محصولات)** | ارسال محدودهٔ مربع‌ها، دریافت محصول پیشنهادی برای نقشه و tooltip |
| ۴ | **نیاز آبی** | ارسال محدودهٔ مربع‌ها، دریافت نیاز آبی هر منطقه برای لایهٔ نیاز آبی |
| ۵ | **کیفیت خاک** | ارسال محدودهٔ مربع‌ها، دریافت کیفیت خاک هر منطقه برای لایهٔ کیفیت خاک |
| ۶ | **ریسک کشت** | ارسال محدودهٔ مربع‌ها، دریافت ریسک کشت هر منطقه برای لایهٔ ریسک کشت |
| ۷ | **دیتای تکمیلی زون** | با کلیک روی هر مربع، دریافت دیتای جزئیات (دلیل، معیارها، نمودار) |

---

## ۰. API منطقهٔ اولیه (Area)

منطقهٔ ثابت زمین که از بک‌اند دریافت می‌شود. کاربر امکان رسم یا ویرایش منطقه را ندارد.

### ۰.۱ مشخصات

- **متد:** `GET`
- **آدرس پیشنهادی:** `GET /api/crop-zoning/area/`
- **هدف:** دریافت polygon منطقهٔ زمین برای نمایش روی نقشه.

### ۰.۲ ورودی (Request)

بدون پارامتر.

### ۰.۳ خروجی (Response Body)

```json
{
  "status": "success",
  "data": {
    "area": {
      "type": "Feature",
      "properties": {},
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [51.38, 35.68],
            [51.40, 35.68],
            [51.40, 35.70],
            [51.38, 35.70],
            [51.38, 35.68]
          ]
        ]
      }
    }
  }
}
```

- **مختصات:** `[longitude, latitude]` طبق استاندارد GeoJSON

---

## ۱. API لیست محصولات و رنگ‌ها

برای نمایش راهنمای رنگ‌ها (Legend) و dropdown انتخاب محصول در پنل جزئیات هر زون.

### ۱.۱ مشخصات

- **متد:** `GET`
- **آدرس پیشنهادی:** `GET /api/crop-zoning/products/` یا `GET /api/crops/`
- **هدف:** دریافت لیست محصولات قابل کشت با رنگ و لیبل نمایشی.

### ۱.۲ ورودی (Request)

بدون پارامتر یا با پارامترهای اختیاری:

| پارامتر | نوع | اجباری | توضیح |
|---------|-----|--------|--------|
| `locale` | string | خیر | کد زبان برای لیبل‌ها (مثلاً `fa`, `en`) |

### ۱.۳ خروجی (Response)

```json
{
  "status": "success",
  "data": {
    "products": [
      {
        "id": "wheat",
        "label": "گندم",
        "color": "#6bcb77"
      },
      {
        "id": "canola",
        "label": "کلزا",
        "color": "#ffd93d"
      },
      {
        "id": "saffron",
        "label": "زعفران",
        "color": "#9b59b6"
      }
    ]
  }
}
```

**ساختار هر محصول:**

| فیلد | نوع | اجباری | توضیح |
|------|-----|--------|--------|
| `id` | string | بله | شناسهٔ یکتا (مثلاً `wheat`, `canola`, `saffron`) |
| `label` | string | بله | نام نمایشی به زبان کاربر |
| `color` | string | بله | رنگ hex برای نمایش روی نقشه و Legend |

---

## ۲. API دیتای اولیه زون‌ها

با رسم منطقهٔ زمین، فرانت **محدودهٔ همهٔ مربع‌ها** (گرید داخل polygon) را ارسال می‌کند و **دیتای اولیه** هر مربع را دریافت می‌کند — برای نمایش نقشه، رنگ‌بندی، و **هاور/tooltip**. این دیتا شامل `reason` و `criteria` **نیست**.

### ۲.۱ مشخصات

- **متد:** `POST`
- **آدرس پیشنهادی:** `POST /api/crop-zoning/zones/initial/`
- **هدف:** ارسال محدودهٔ مربع‌ها، دریافت دیتای اولیه برای نقشه، هاور و tooltip.

### ۲.۲ ورودی (Request Body)

فرانت ابتدا با Turf.js از روی polygon منطقه گرید می‌سازد، سپس `FeatureCollection` همهٔ polygonهای مربع‌ها را ارسال می‌کند.

| فیلد | نوع | اجباری | توضیح |
|------|-----|--------|--------|
| `zones` | GeoJSON FeatureCollection | بله | محدودهٔ هر مربع به صورت Polygon؛ ترتیب index با پاسخ یکسان است |
| `products` | string[] | خیر | لیست محصولات مدنظر؛ در صورت عدم ارسال از همهٔ محصولات استفاده شود |

**ساختار `zones` (محدودهٔ همهٔ مربع‌ها):**

```json
{
  "zones": {
    "type": "FeatureCollection",
    "features": [
      {
        "type": "Feature",
        "geometry": {
          "type": "Polygon",
          "coordinates": [
            [
              [51.38, 35.68],
              [51.3815, 35.68],
              [51.3815, 35.6815],
              [51.38, 35.6815],
              [51.38, 35.68]
            ]
          ]
        },
        "properties": { "index": 0 }
      },
      {
        "type": "Feature",
        "geometry": {
          "type": "Polygon",
          "coordinates": [
            [
              [51.3815, 35.68],
              [51.383, 35.68],
              [51.383, 35.6815],
              [51.3815, 35.6815],
              [51.3815, 35.68]
            ]
          ]
        },
        "properties": { "index": 1 }
      }
    ]
  },
  "products": ["wheat", "canola", "saffron"]
}
```

- **مختصات:** `[longitude, latitude]` طبق استاندارد GeoJSON
- **index:** در `properties` هر feature برای تطابق با پاسخ (اختیاری؛ در صورت نبودن از ترتیب آرایه استفاده شود)

### ۲.۳ خروجی (Response Body) — دیتای اولیه

فقط فیلدهای لازم برای **نقشه**، **هاور** و **tooltip** (نمایش هنگام عبور ماوس روی هر مربع)؛ بدون `reason` و `criteria`.

```json
{
  "status": "success",
  "data": {
    "total_area_hectares": 23.45,
    "total_area_sqm": 234500,
    "zone_count": 3,
    "zones": [
      {
        "zoneId": "zone-0",
        "geometry": {
          "type": "Polygon",
          "coordinates": [
            [
              [51.38, 35.68],
              [51.3815, 35.68],
              [51.3815, 35.6815],
              [51.38, 35.6815],
              [51.38, 35.68]
            ]
          ]
        },
        "crop": "wheat",
        "matchPercent": 85,
        "waterNeed": "۴۵۰۰-۵۵۰۰ m³/ha",
        "estimatedProfit": "۱۵-۲۵ میلیون/هکتار"
      },
      {
        "zoneId": "zone-1",
        "geometry": { "type": "Polygon", "coordinates": [...] },
        "crop": "canola",
        "matchPercent": 78,
        "waterNeed": "۵۰۰۰-۶۰۰۰ m³/ha",
        "estimatedProfit": "۲۰-۳۵ میلیون/هکتار"
      }
    ]
  }
}
```

**ساختار دیتای اولیه هر زون (هم برای نقشه هم برای هاور/tooltip):**

| فیلد | نوع | اجباری | توضیح |
|------|-----|--------|--------|
| `zoneId` | string | بله | شناسهٔ یکتا برای درخواست دیتای تکمیلی |
| `geometry` | Polygon | بله | هندسهٔ همان مربع ارسالی |
| `crop` | string \| null | خیر | محصول پیشنهادی؛ اگر `null`/خالی/`uncultivable` باشد → زون **غیرقابل کشت** و رنگ خاکستری |
| `matchPercent` | number | خیر | درصد تطابق (هاور/tooltip) |
| `waterNeed` | string | خیر | نیاز آبی (هاور/tooltip) |
| `estimatedProfit` | string | خیر | سود تخمینی (هاور/tooltip) |

**زون غیرقابل کشت:** اگر برای مربعی اطلاعاتی نیاید یا `crop` خالی/`null`/`uncultivable` باشد، آن مربع خاکستری نمایش داده شده و در tooltip «غیر قابل کشت» نشان داده می‌شود. کلیک روی آن پنل جزئیات باز نمی‌شود.

**نکته:** این فیلدها هنگام **هاور** روی مربع در tooltip نمایش داده می‌شوند؛ نیازی به درخواست جداگانه برای tooltip نیست.

---

## ۲.۱ API نیاز آبی (Water Need)

نیاز آبی هر منطقه را بر اساس محدودهٔ مربع‌ها برمی‌گرداند. با تغییر لایه به «نیاز آبی» در LayerControl، فرانت این API را صدا می‌زند و نقشه و Legend را به‌روزرسانی می‌کند.

### مشخصات

- **متد:** `POST`
- **آدرس پیشنهادی:** `POST /api/crop-zoning/zones/water-need/`
- **هدف:** دریافت نیاز آبی هر منطقه برای نمایش روی نقشه در لایهٔ نیاز آبی.

### ورودی (Request Body)

همان ساختار `POST zones/initial/`:

| فیلد | نوع | اجباری | توضیح |
|------|-----|--------|--------|
| `zones` | GeoJSON FeatureCollection | بله | محدودهٔ هر مربع به صورت Polygon |

### خروجی (Response Body)

```json
{
  "status": "success",
  "data": {
    "zones": [
      {
        "zoneId": "zone-0",
        "geometry": { "type": "Polygon", "coordinates": [...] },
        "level": "low",
        "value": "۳۰۰۰-۴۰۰۰ m³/ha",
        "color": "#7dd3fc"
      },
      {
        "zoneId": "zone-1",
        "geometry": { "type": "Polygon", "coordinates": [...] },
        "level": "medium",
        "value": "۵۰۰۰-۶۰۰۰ m³/ha",
        "color": "#0ea5e9"
      }
    ]
  }
}
```

| فیلد | نوع | توضیح |
|------|-----|--------|
| `zoneId` | string | شناسهٔ زون |
| `geometry` | Polygon | هندسهٔ مربع |
| `level` | string | سطح: `low`, `medium`, `high` |
| `value` | string | مقدار نیاز آبی (مثلاً m³/ha) |
| `color` | string | رنگ hex برای نمایش |

---

## ۲.۲ API کیفیت خاک (Soil Quality)

کیفیت خاک هر منطقه را برمی‌گرداند. با تغییر لایه به «کیفیت خاک»، فرانت این API را صدا می‌زند.

### مشخصات

- **متد:** `POST`
- **آدرس پیشنهادی:** `POST /api/crop-zoning/zones/soil-quality/`

### ورودی (Request Body)

همان `zones` (FeatureCollection).

### خروجی (Response Body)

```json
{
  "status": "success",
  "data": {
    "zones": [
      {
        "zoneId": "zone-0",
        "geometry": { "type": "Polygon", "coordinates": [...] },
        "level": "low",
        "score": 35,
        "color": "#f87171"
      },
      {
        "zoneId": "zone-1",
        "geometry": { "type": "Polygon", "coordinates": [...] },
        "level": "high",
        "score": 85,
        "color": "#22c55e"
      }
    ]
  }
}
```

| فیلد | نوع | توضیح |
|------|-----|--------|
| `level` | string | سطح: `low`, `medium`, `high` |
| `score` | number | امتیاز ۰–۱۰۰ |
| `color` | string | رنگ hex |

---

## ۲.۳ API ریسک کشت (Cultivation Risk)

ریسک کشت هر منطقه را برمی‌گرداند. با تغییر لایه به «ریسک کشت»، فرانت این API را صدا می‌زند.

### مشخصات

- **متد:** `POST`
- **آدرس پیشنهادی:** `POST /api/crop-zoning/zones/cultivation-risk/`

### ورودی و خروجی

ورودی: همان `zones` (FeatureCollection).

خروجی نمونه:

```json
{
  "status": "success",
  "data": {
    "zones": [
      {
        "zoneId": "zone-0",
        "geometry": { "type": "Polygon", "coordinates": [...] },
        "level": "low",
        "color": "#22c55e"
      },
      {
        "zoneId": "zone-1",
        "geometry": { "type": "Polygon", "coordinates": [...] },
        "level": "high",
        "color": "#ef4444"
      }
    ]
  }
}
```

| فیلد | نوع | توضیح |
|------|-----|--------|
| `level` | string | سطح: `low`, `medium`, `high` |
| `color` | string | رنگ hex |

**نکته:** برای هر لایه (نیاز آبی، کیفیت خاک، ریسک کشت) فرانت یک **درخواست جداگانه** ارسال می‌کند و نقشه و Legend متناسب با همان لایه به‌روزرسانی می‌شوند.

---

## ۳. API دیتای تکمیلی زون (با کلیک روی مربع)

وقتی کاربر روی یک مربع کلیک می‌کند، فرانت با `zoneId` دیتای **تکمیلی** را درخواست می‌کند — برای نمایش پنل جزئیات: دلیل پیشنهاد، معیارها، نمودار راداری.

### ۳.۱ مشخصات

- **متد:** `GET`
- **آدرس پیشنهادی:** `GET /api/crop-zoning/zones/:zoneId/details/`
- **هدف:** دریافت دیتای تکمیلی یک زون برای پنل جزئیات.

### ۳.۲ ورودی (Request)

| پارامتر | محل | نوع | اجباری | توضیح |
|---------|------|-----|--------|--------|
| `zoneId` | path | string | بله | شناسهٔ زون (مثلاً `zone-0`) |

**مثال:** `GET /api/crop-zoning/zones/zone-0/details/`

### ۳.۳ خروجی (Response Body)

```json
{
  "status": "success",
  "data": {
    "zoneId": "zone-0",
    "crop": "wheat",
    "matchPercent": 85,
    "waterNeed": "۴۵۰۰-۵۵۰۰ m³/ha",
    "estimatedProfit": "۱۵-۲۵ میلیون/هکتار",
    "reason": "دمای مناسب، خاک حاصلخیز، دسترسی به آب کافی",
    "criteria": [
      { "name": "دما", "value": 82 },
      { "name": "بارش", "value": 75 },
      { "name": "خاک", "value": 88 },
      { "name": "آب", "value": 70 }
    ],
    "area_hectares": 2.25
  }
}
```

**فیلدهای دیتای تکمیلی:**

| فیلد | نوع | اجباری | توضیح |
|------|-----|--------|--------|
| `zoneId` | string | بله | همان zoneId درخواست |
| `crop` | string | بله | محصول پیشنهادی |
| `matchPercent` | number | بله | درصد تطابق |
| `waterNeed` | string | بله | نیاز آبی |
| `estimatedProfit` | string | بله | سود تخمینی |
| `reason` | string | بله | **فقط در دیتای تکمیلی** — دلیل پیشنهاد محصول |
| `criteria` | object[] | بله | **فقط در دیتای تکمیلی** — معیارها برای نمودار راداری |
| `area_hectares` | number | خیر | مساحت این زون بر حسب هکتار |

### ۳.۴ ساختار `criteria`

| فیلد | نوع | توضیح |
|------|-----|--------|
| `name` | string | نام معیار (دما، بارش، خاک، آب) |
| `value` | number | امتیاز ۰–۱۰۰ |

---

## ۴. مساحت کلی (Total Area)

در پاسخ **API دیتای اولیه زون‌ها** برمی‌گردد:

| فیلد | نوع | توضیح |
|------|-----|--------|
| `total_area_hectares` | number | مساحت کل منطقه بر حسب هکتار |
| `total_area_sqm` | number | مساحت کل بر حسب متر مربع |

---

## ۵. خلاصهٔ ساختار‌های مورد نیاز فرانت

### دیتای اولیه زون (برای نقشه و هاور/tooltip)

```ts
interface ZoneInitialData {
  zoneId: string
  geometry: Polygon
  crop: string
  matchPercent: number
  waterNeed: string
  estimatedProfit: string
}
```

### دیتای تکمیلی زون (برای پنل جزئیات — پس از کلیک)

```ts
interface ZoneDetailData {
  zoneId: string
  crop: string
  matchPercent: number
  waterNeed: string
  estimatedProfit: string
  reason: string
  criteria: { name: string; value: number }[]
  area_hectares?: number
}
```

### محصولات و رنگ‌ها (پیش‌فرض فرانت)

```ts
const CROP_COLORS: Record<CropType, string> = {
  wheat: '#6bcb77',
  canola: '#ffd93d',
  saffron: '#9b59b6'
}
```

---

## ۶. جریان فرانت با APIها

1. **لود صفحه:** `GET /api/crop-zoning/products/` → لیست محصولات و رنگ‌ها.
2. **رسم منطقه / بهینه‌سازی:** فرانت با Turf از polygon منطقه گرید می‌سازد → `POST /api/crop-zoning/zones/initial/` با `zones` (FeatureCollection) → نقشه و tooltip با دیتای محصولات رسم می‌شود.
3. **تغییر لایه در LayerControl:** برای هر لایه یک درخواست جداگانه ارسال می‌شود:
   - محصولات پیشنهادی: `POST zones/initial/` (در مرحلهٔ ۲)
   - نیاز آبی: `POST zones/water-need/` → نقشه و Legend به‌روزرسانی می‌شوند
   - کیفیت خاک: `POST zones/soil-quality/` → نقشه و Legend به‌روزرسانی می‌شوند
   - ریسک کشت: `POST zones/cultivation-risk/` → نقشه و Legend به‌روزرسانی می‌شوند
4. **کلیک روی مربع:** `GET /api/crop-zoning/zones/{zoneId}/details/` → دیتای تکمیلی → پنل جزئیات باز می‌شود (reason, criteria, نمودار راداری).

---

## ۷. وضعیت فعلی و نیازمندی‌ها

- در حال حاضر زون‌بندی با **دیتای ماک** و الگوریتم محلی (`createZonedGrid` در `cropZoningUtils.ts`) کار می‌کند.
- برای اتصال به بک‌اند، لازم است:
  1. سرویس `cropZoningService` با سه endpoint: `getProducts()`, `getZonesInitial(zones)`, `getZoneDetails(zoneId)` ایجاد شود.
  2. در `CropZoningMap` به جای `createZonedGrid` ابتدا گرید با Turf ساخته شود، سپس `zones` به API ارسال و پاسخ برای رسم استفاده شود.
  3. در `onZoneClick` قبل از باز کردن پنل، `getZoneDetails(zoneId)` صدا زده شود و دیتای تکمیلی به `ZoneDetailPanel` پاس داده شود.
  4. مساحت کلی (`total_area_hectares`) در پاسخ initial در UI نمایش داده شود.
