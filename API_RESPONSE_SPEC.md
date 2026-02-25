# مشخصات Response های API بخش Crop Zoning

این سند فقط **فرمت و ساختار response**هایی را که فرانت‌اند از API انتظار دارد شرح می‌دهد.

---

## ۱. API بهینه‌سازی زون‌بندی (Optimize Zoning)

وقتی کاربر منطقه را روی نقشه انتخاب می‌کند و دکمه «بهینه‌سازی مجدد» را می‌زند، فرانت‌اند یک **GeoJSON Polygon** (مختصات منطقه) به API می‌فرستد و انتظار دارد سرور یک **GeoJSON FeatureCollection** برگرداند که هر feature آن یک زون با geometry (چندضلعی) و properties (داده‌های پیشنهاد محصول) دارد.

### Request (خلاصه)

- **ورودی:** یک GeoJSON به صورت `Feature` با `geometry.type: "Polygon"` (مختصات به صورت `[lng, lat]`).

### Response مورد انتظار

یک **GeoJSON FeatureCollection** با این ساختار:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[lng, lat], [lng, lat], ...]]
      },
      "properties": {
        "zoneId": "string",
        "crop": "wheat" | "canola" | "saffron",
        "matchPercent": number,
        "waterNeed": "string",
        "estimatedProfit": "string",
        "reason": "string",
        "criteria": [
          { "name": "string", "value": number },
          ...
        ]
      }
    }
  ]
}
```

### توضیح فیلدهای `properties` هر زون

| فیلد | نوع | توضیح |
|------|-----|--------|
| `zoneId` | `string` | شناسه یکتا برای زون (مثلاً `"zone-0"`, `"zone-1"`) |
| `crop` | `"wheat" \| "canola" \| "saffron"` | نوع محصول پیشنهادی برای این زون |
| `matchPercent` | `number` | درصد تطابق (۰–۱۰۰) برای پیشنهاد محصول |
| `waterNeed` | `string` | نیاز آبی (مثلاً `"۴۵۰۰-۵۵۰۰ m³/ha"`) |
| `estimatedProfit` | `string` | سود تخمینی (مثلاً `"۱۵-۲۵ میلیون/هکتار"`) |
| `reason` | `string` | توضیح کوتاه دلیل پیشنهاد این محصول |
| `criteria` | `Array<{ name: string, value: number }>` | معیارهای امتیازدهی برای نمودار راداری؛ `value` بین ۰ تا ۱۰۰ (مثلاً دما، بارش، خاک، آب) |

### نمونه response (یک feature)

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [51.38, 35.68],
            [51.381, 35.68],
            [51.381, 35.681],
            [51.38, 35.681],
            [51.38, 35.68]
          ]
        ]
      },
      "properties": {
        "zoneId": "zone-0",
        "crop": "wheat",
        "matchPercent": 78,
        "waterNeed": "۴۵۰۰-۵۵۰۰ m³/ha",
        "estimatedProfit": "۱۵-۲۵ میلیون/هکتار",
        "reason": "دمای مناسب، خاک حاصلخیز، دسترسی به آب کافی",
        "criteria": [
          { "name": "دما", "value": 85 },
          { "name": "بارش", "value": 72 },
          { "name": "خاک", "value": 80 },
          { "name": "آب", "value": 65 }
        ]
      }
    }
  ]
}
```

---

## ۲. API منطقه اولیه (اختیاری)

اگر بخواهید منطقه اولیه نقشه از سرور بیاید (به‌جای ماک ثابت)، response باید یک **GeoJSON Feature** با Polygon باشد:

```json
{
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
```

- مختصات به صورت `[longitude, latitude]` (lng, lat).
- آرایه اول `coordinates` حلقه بیرونی چندضلعی است؛ نقطه اول و آخر باید یکسان باشند.

---

## ۳. خلاصه نوع‌های TypeScript (برای تطبیق با بک‌اند)

```ts
type CropType = 'wheat' | 'canola' | 'saffron'

interface ZoneFeatureProperties {
  zoneId: string
  crop: CropType
  matchPercent: number
  waterNeed: string
  estimatedProfit: string
  reason: string
  criteria: { name: string; value: number }[]
}

// Response بهینه‌سازی = GeoJSON FeatureCollection
// با Feature<Polygon, ZoneFeatureProperties>
```

---

## ۴. نکات

- **Layer فعلی:** فرانت‌اند لایه‌های مختلف (`crops`, `waterNeed`, `soilQuality`, `cultivationRisk`) دارد؛ در صورت نیاز می‌توان برای هر لایه response جدا یا فیلدهای اضافه در `properties` تعریف کرد.
- **دکمه «تغییر محصول»:** در پنل جزئیات زون، کاربر می‌تواند محصول را بین `wheat`, `canola`, `saffron` عوض کند؛ در صورت نیاز می‌توان API جدا برای ذخیره این تغییر تعریف کرد.
- **بخش آب و هوا:** داده‌های آب و هوا از سرویس جدا (`farmDashboardService.getAllCards()` → `farmWeatherCard`) گرفته می‌شوند و در این سند پوشش داده نشده‌اند.
