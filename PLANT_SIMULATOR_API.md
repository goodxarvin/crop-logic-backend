# قرارداد API شبیه‌ساز گیاه (Plant Simulator)

این سند تمام داده‌هایی را که باید **از بکند بیاید**، **به بکند فرستاده شود** و دوباره **از بکند برگردد** به‌همراه ساختار و داده‌های ماک توصیف می‌کند.

---

## ۱. داده‌های اولیه (از بکند → فرانت)

این داده‌ها یک‌بار هنگام لود صفحه (یا هنگام باز کردن شبیه‌ساز) از بکند گرفته می‌شوند.

### ۱.۱ تنظیمات اسلایدرها (کنترل‌های محیطی)

هر اسلایدر (نور، آب، pH خاک، سرعت رشد و غیره) باید از بکند **حداقل، حداکثر، گام، واحد و برچسب** بگیرد. واحد می‌تواند درصد (`percent`) یا عدد با واحد متنی (`number` + `unit`) باشد.

```ts
// GET /api/plant-simulator/config  یا بخشی از همین endpoint

interface SliderConfig {
  key: string           // مثلاً: "light" | "water" | "soil_ph" | "growth_speed"
  label: string         // برچسب نمایشی (مثلاً "نور"، "آب")
  min: number
  max: number
  step: number
  unit_type: 'percent' | 'number'
  unit?: string         // وقتی unit_type === 'number' مثلاً "g/s", "ppm", "°C"
  default_value: number
  icon?: string         // اختیاری: مثلاً "☀️", "💧"
}

// پاسخ نمونه
{
  "sliders": [
    {
      "key": "light",
      "label": "نور",
      "min": 0,
      "max": 100,
      "step": 5,
      "unit_type": "percent",
      "default_value": 75,
      "icon": "☀️"
    },
    {
      "key": "water",
      "label": "آب",
      "min": 0,
      "max": 100,
      "step": 5,
      "unit_type": "percent",
      "default_value": 65,
      "icon": "💧"
    },
    {
      "key": "soil_ph",
      "label": "pH خاک",
      "min": 4,
      "max": 9,
      "step": 0.5,
      "unit_type": "number",
      "unit": "",
      "default_value": 6.5
    },
    {
      "key": "growth_speed",
      "label": "سرعت رشد",
      "min": 0.5,
      "max": 5,
      "step": 0.5,
      "unit_type": "number",
      "unit": "×",
      "default_value": 1.5
    }
  ]
}
```

### ۱.۲ ثابت‌های شبیه‌ساز (حداکثرها و محدوده چارت)

برای نمایش صحیح ارتفاع، برگ، شاخه، میوه، محصول و محورهای چارت باید از بکند بیاید.

```ts
// همان config یا GET /api/plant-simulator/constants

interface SimulatorConstants {
  max_height: number      // مثلاً 280 (px یا واحد ارتفاع)
  max_leaves: number      // مثلاً 14
  max_branches: number    // مثلاً 6
  max_yield: number       // مثلاً 500 (گرم)
  yield_unit: string      // مثلاً "g"
  yield_rate_unit: string // مثلاً "g/s"
  height_unit?: string    // مثلاً "px" یا "cm"
}

// پاسخ نمونه
{
  "max_height": 280,
  "max_leaves": 14,
  "max_branches": 6,
  "max_yield": 500,
  "yield_unit": "g",
  "yield_rate_unit": "g/s",
  "height_unit": "px"
}
```

### ۱.۳ تنظیمات چارت (محورها و سری‌ها)

عنوان چارت، برچسب محورها و محدوده min/max هر محور تا در فرانت به‌درستی رسم شود.

```ts
interface ChartConfig {
  title: string
  x_axis_label?: string       // مثلاً "زمان (ثانیه)"
  series: {
    key: string                // "height" | "leaves" | "yield" | "yield_rate"
    label: string
    y_axis_id: string          // "yHeight" | "yLeaf" | "yYield" | "yYieldRate"
    min: number
    max: number
    unit?: string
  }[]
}

// پاسخ نمونه
{
  "chart": {
    "title": "پیشرفت رشد",
    "x_axis_label": "زمان (ثانیه)",
    "series": [
      { "key": "height", "label": "ارتفاع (px)", "y_axis_id": "yHeight", "min": 0, "max": 280, "unit": "px" },
      { "key": "leaves", "label": "تعداد برگ", "y_axis_id": "yLeaf", "min": 0, "max": 14 },
      { "key": "yield", "label": "محصول (g)", "y_axis_id": "yYield", "min": 0, "max": 500, "unit": "g" },
      { "key": "yield_rate", "label": "نرخ محصول (g/s)", "y_axis_id": "yYieldRate", "min": 0, "unit": "g/s" }
    ]
  }
}
```

---

## ۲. داده‌هایی که به بکند فرستاده می‌شوند

### ۲.۱ شروع شبیه‌سازی

وقتی کاربر دکمه «شروع» را می‌زند، مقادیر فعلی محیط و سرعت به بکند ارسال می‌شود.

```ts
// POST /api/plant-simulator/start

interface StartSimulationRequest {
  environment: Record<string, number>  // key مطابق slider.key ها
  growth_speed: number
}

// مثال
{
  "environment": {
    "light": 75,
    "water": 65,
    "soil_ph": 6.5
  },
  "growth_speed": 1.5
}
```

### ۲.۲ توقف شبیه‌سازی

```ts
// POST /api/plant-simulator/stop

// بدنه خالی یا فقط session_id در صورت نیاز
{}
```

### ۲.۳ ریست

```ts
// POST /api/plant-simulator/reset

// بدنه خالی یا session_id
{}
```

### ۲.۴ به‌روزرسانی محیط (تغییر اسلایدرها)

هر بار کاربر نور، آب، pH یا سرعت را عوض کند، در حالت real-time می‌توان این را به بکند فرستاد (اختیاری؛ بکند می‌تواند فقط با start این مقادیر را بگیرد).

```ts
// PATCH /api/plant-simulator/environment

interface UpdateEnvironmentRequest {
  environment: Record<string, number>
  growth_speed?: number
}

// مثال
{
  "environment": { "light": 80, "water": 70, "soil_ph": 6.5 },
  "growth_speed": 2
}
```

---

## ۳. داده‌هایی که از بکند برمی‌گردند (حین / بعد شبیه‌سازی)

این داده‌ها یا با **polling** (مثلاً هر ۱ ثانیه) یا با **WebSocket/SSE** از بکند گرفته می‌شوند و در UI و چارت به‌صورت تدریجی به‌روز می‌شوند (مثلاً آرایه‌های چارت کم‌کم طولانی می‌شوند).

### ۳.۱ وضعیت گیاه (آمار کارت بالا)

تعداد برگ، شاخه، میوه، ارتفاع، محصول و نرخ محصول باید از بکند بیاید تا با سرعت رشد واقعی همگام باشد.

```ts
// GET /api/plant-simulator/state  یا از طریق WebSocket

interface PlantStateResponse {
  height: number
  leaves_count: number
  branches_count: number
  fruits_count: number
  yield: number
  yield_rate: number
  tick: number
  is_healthy: boolean        // آیا گیاه می‌تواند به سلامت به رشد ادامه دهد؟
  can_continue: boolean      // معادل is_healthy یا منطق جدا (مثلاً رسیدن به حداکثر ارتفاع)
}

// پاسخ نمونه (یک لحظه از زمان)
{
  "height": 120,
  "leaves_count": 4,
  "branches_count": 2,
  "fruits_count": 0,
  "yield": 0,
  "yield_rate": 0.012,
  "tick": 340,
  "is_healthy": true,
  "can_continue": true
}
```

### ۳.۲ پیشرفت و وضعیت نوارهای پیشرفت

پیشرفت رشد، وضعیت نور، وضعیت آب و محصول‌دهی برای نوارهای پیشرفت (Progress) و نمایش درصد/عدد.

```ts
interface ProgressResponse {
  growth_progress: number    // 0..100 (بر اساس height / max_height)
  light_status: number       // مقدار فعلی نور (مثلاً 0..100 درصد)
  water_status: number       // مقدار فعلی آب (مثلاً 0..100 درصد)
  yield_progress: number     // 0..100 (بر اساس yield / max_yield)
  yield_current: number
  yield_rate_current: number
}

// پاسخ نمونه
{
  "growth_progress": 42,
  "light_status": 75,
  "water_status": 65,
  "yield_progress": 8,
  "yield_current": 42.5,
  "yield_rate_current": 0.093
}
```

این فیلدها می‌توانند داخل همان `PlantStateResponse` یا در یک endpoint جدا برگردانده شوند.

### ۳.۳ داده‌های چارت (تاریخچهٔ زمانی)

داده‌های چارت به‌صورت آرایه‌هایی هستند که **بر اساس زمان (مثلاً هر ثانیه) از بکند پر می‌شوند**. فرانت این آرایه‌ها را مستقیم به نمودار می‌دهد؛ هر نقطهٔ جدید با سرعت رشد گیاه اضافه می‌شود.

مثال: اگر بکند هر ثانیه یک بار state بفرستد، آرایه‌ها به این شکل طول می‌کشند:

- ثانیه ۰: `[0]`
- ثانیه ۱: `[0, 5]`
- ثانیه ۲: `[0, 5, 10]`
- ثانیه ۳: `[0, 5, 10, 30]`
- ثانیه ۴: `[0, 5, 10, 30, 40]`

یعنی **مقادیر با سرعت رشد گیاه کم‌کم به آرایه اضافه می‌شوند**.

```ts
// GET /api/plant-simulator/state  یا بخشی از همان پاسخ

interface ChartHistoryResponse {
  labels: string[]           // مثلاً ["0s", "1s", "2s", ...]
  height_history: number[]
  leaf_history: number[]
  yield_history: number[]
  yield_rate_history: number[]
}

// پاسخ نمونه (بعد از چند ثانیه شبیه‌سازی)
{
  "labels": ["0s", "1s", "2s", "3s", "4s", "5s"],
  "height_history": [0, 5, 12, 28, 45, 68],
  "leaf_history": [0, 0, 1, 2, 3, 4],
  "yield_history": [0, 0, 0, 0.1, 0.5, 1.2],
  "yield_rate_history": [0, 0, 0, 0.01, 0.03, 0.06]
}
```

- **ارتفاع (height_history)**: مقدار ارتفاع در هر نمونه (مثلاً هر ثانیه).
- **برگ (leaf_history)**: تعداد برگ در هر نمونه.
- **محصول (yield_history)**: مقدار تجمعی محصول (g) در هر نمونه.
- **نرخ محصول (yield_rate_history)**: نرخ لحظه‌ای (g/s) در هر نمونه.

محتوای داخل چارت دقیقاً همین آرایه‌هاست؛ فرانت فقط این‌ها را روی محور زمان رسم می‌کند و با هر پاسخ جدید یک (یا چند) نقطه به انتهای آرایه اضافه می‌شود.

---

## ۴. خلاصهٔ جریان داده

| جهت | زمان | داده |
|-----|------|------|
| بکند → فرانت | لود صفحه | Config: اسلایدرها (min, max, step, unit)، ثابت‌ها (max_height, max_leaves, ...)، تنظیمات چارت |
| فرانت → بکند | کلیک شروع | محیط (light, water, soil_ph, ...) و growth_speed |
| فرانت → بکند | کلیک توقف / ریست | stop یا reset |
| فرانت → بکند | (اختیاری) تغییر اسلایدر | environment + growth_speed |
| بکند → فرانت | حین شبیه‌سازی (polling/WS) | PlantState (height, leaves_count, branches_count, fruits_count, yield, yield_rate, is_healthy, can_continue) |
| بکند → فرانت | همان پاسخ | Progress (growth_progress, light_status, water_status, yield_progress, yield_current, yield_rate_current) |
| بکند → فرانت | همان پاسخ | ChartHistory (labels, height_history, leaf_history, yield_history, yield_rate_history) |

---

## ۵. داده‌های ماک (Mock) کامل

برای توسعه و تست فرانت بدون بکند می‌توان از این ماک استفاده کرد.

### ۵.۱ ماک Config (اسلایدرها + ثابت‌ها + چارت)

```json
{
  "sliders": [
    {
      "key": "light",
      "label": "نور",
      "min": 0,
      "max": 100,
      "step": 5,
      "unit_type": "percent",
      "default_value": 75,
      "icon": "☀️"
    },
    {
      "key": "water",
      "label": "آب",
      "min": 0,
      "max": 100,
      "step": 5,
      "unit_type": "percent",
      "default_value": 65,
      "icon": "💧"
    },
    {
      "key": "soil_ph",
      "label": "pH خاک",
      "min": 4,
      "max": 9,
      "step": 0.5,
      "unit_type": "number",
      "unit": "",
      "default_value": 6.5
    },
    {
      "key": "growth_speed",
      "label": "سرعت رشد",
      "min": 0.5,
      "max": 5,
      "step": 0.5,
      "unit_type": "number",
      "unit": "×",
      "default_value": 1.5
    }
  ],
  "constants": {
    "max_height": 280,
    "max_leaves": 14,
    "max_branches": 6,
    "max_yield": 500,
    "yield_unit": "g",
    "yield_rate_unit": "g/s",
    "height_unit": "px"
  },
  "chart": {
    "title": "پیشرفت رشد",
    "x_axis_label": "زمان (ثانیه)",
    "series": [
      { "key": "height", "label": "ارتفاع (px)", "y_axis_id": "yHeight", "min": 0, "max": 280, "unit": "px" },
      { "key": "leaves", "label": "تعداد برگ", "y_axis_id": "yLeaf", "min": 0, "max": 14 },
      { "key": "yield", "label": "محصول (g)", "y_axis_id": "yYield", "min": 0, "max": 500, "unit": "g" },
      { "key": "yield_rate", "label": "نرخ محصول (g/s)", "y_axis_id": "yYieldRate", "min": 0, "unit": "g/s" }
    ]
  }
}
```

### ۵.۲ ماک State + Progress + Chart (یک پاسخ ترکیبی)

```json
{
  "plant": {
    "height": 142,
    "leaves_count": 5,
    "branches_count": 2,
    "fruits_count": 0,
    "yield": 12.4,
    "yield_rate": 0.087,
    "tick": 520,
    "is_healthy": true,
    "can_continue": true
  },
  "progress": {
    "growth_progress": 50,
    "light_status": 75,
    "water_status": 65,
    "yield_progress": 2.5,
    "yield_current": 12.4,
    "yield_rate_current": 0.087
  },
  "chart": {
    "labels": ["0s", "1s", "2s", "3s", "4s", "5s", "6s", "7s", "8s", "9s", "10s"],
    "height_history": [0, 5, 12, 28, 45, 68, 92, 110, 125, 135, 142],
    "leaf_history": [0, 0, 1, 2, 3, 4, 4, 5, 5, 5, 5],
    "yield_history": [0, 0, 0, 0.1, 0.5, 1.2, 3.2, 5.8, 8.2, 10.1, 12.4],
    "yield_rate_history": [0, 0, 0, 0.01, 0.03, 0.05, 0.06, 0.07, 0.08, 0.085, 0.087]
  }
}
```

### ۵.۳ ماک برای نمایش تدریجی چارت

چارت باید بر اساس همین آرایه‌ها به‌صورت تدریجی پر شود؛ هر بار بکند state جدید می‌فرستد، یک نقطه به انتهای هر آرایه اضافه می‌شود. مثال برای چند لحظهٔ متوالی:

```json
// t=0
{ "labels": ["0s"], "height_history": [0], "leaf_history": [0], "yield_history": [0], "yield_rate_history": [0] }

// t=1s
{ "labels": ["0s", "1s"], "height_history": [0, 5], "leaf_history": [0, 0], "yield_history": [0, 0], "yield_rate_history": [0, 0] }

// t=2s
{ "labels": ["0s", "1s", "2s"], "height_history": [0, 5, 12], "leaf_history": [0, 0, 1], "yield_history": [0, 0, 0], "yield_rate_history": [0, 0, 0] }

// t=3s
{ "labels": ["0s", "1s", "2s", "3s"], "height_history": [0, 5, 12, 30], "leaf_history": [0, 0, 1, 2], "yield_history": [0, 0, 0, 0.1], "yield_rate_history": [0, 0, 0, 0.01] }

// t=4s
{ "labels": ["0s", "1s", "2s", "3s", "4s"], "height_history": [0, 5, 12, 30, 48], "leaf_history": [0, 0, 1, 2, 3], "yield_history": [0, 0, 0, 0.1, 0.5], "yield_rate_history": [0, 0, 0, 0.01, 0.03] }
```

ارتفاع و بقیهٔ مقادیر باید متناسب با سرعت رشد و منطق بکند افزایش یابند؛ اعداد بالا فقط نمونهٔ ماک هستند.

---

## ۶. نکات پیاده‌سازی فرانت

- **اسلایدرها**: با استفاده از `sliders` از config، هر کنترل با `min`, `max`, `step`, `unit_type`, `unit` و `default_value` رندر شود.
- **آمار کارت (ارتفاع، برگ، شاخه، میوه، محصول، نرخ)**: مستقیم از `plant` در پاسخ state.
- **سلامت گیاه**: با `is_healthy` و `can_continue` می‌توان پیام یا استایل متفاوت نشان داد (مثلاً هشدار وقتی `can_continue === false`).
- **نوارهای پیشرفت**: از `progress` برای پیشرفت رشد، وضعیت نور، وضعیت آب و محصول‌دهی.
- **چارت**: فقط `chart.labels` و آرایه‌های `height_history`, `leaf_history`, `yield_history`, `yield_rate_history` را به کامپوننت نمودار بدهید؛ با هر پاسخ جدید آرایه‌ها طولانی می‌شوند و نمودار به‌صورت تدریجی به‌روز می‌شود.

اگر endpointها یا فیلدهای اضافه‌ای در بکند دارید، می‌توان آنها را به همین سند اضافه کرد تا فرانت و بکند همیشه هم‌خوان باشند.
