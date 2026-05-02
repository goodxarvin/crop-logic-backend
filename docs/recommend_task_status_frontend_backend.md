# Recommend Task Status API Guide

این فایل برای تیم فرانت‌اند توضیح می‌دهد که برای ماژول‌های `fertilization` و `irrigation` چه درخواست‌هایی باید به بک‌اند ارسال شود و چه پاسخ‌هایی باید دریافت شود.

## Fertilization Recommendation

### 1) ثبت درخواست پیشنهاد

**Endpoint**

`POST /api/fertilization-recommendation/recommend/`

**Request Body**

```json
{
  "crop_id": "wheat",
  "growth_stage": "tillering",
  "farm_data": {
    "soilType": "loam",
    "organicMatter": "medium",
    "waterEC": "1.2"
  },
  "soilType": "loam",
  "organicMatter": "medium",
  "waterEC": "1.2"
}
```

**Field Description**

- `crop_id`: شناسه محصول
- `growth_stage`: مرحله رشد محصول
- `farm_data.soilType`: نوع خاک
- `farm_data.organicMatter`: مقدار ماده آلی
- `farm_data.waterEC`: EC آب
- `soilType`, `organicMatter`, `waterEC`: همین داده‌ها اگر فرانت بخواهد به صورت flat هم ارسال کند

**Success Response**

اگر سرویس خارجی مستقیم نتیجه را برگرداند:

```json
{
  "status": "success",
  "data": {
    "plan": {
      "npkRatio": "20-20-20",
      "amountPerHectare": "150 kg/ha",
      "applicationMethod": "drip",
      "applicationInterval": "every 14 days",
      "reasoning": "balanced nutrition for current growth stage"
    }
  }
}
```

اگر سرویس خارجی async باشد، معمولاً `task_id` برمی‌گرداند:

```json
{
  "status": "success",
  "data": {
    "task_id": "fert-task-123",
    "status": "pending"
  }
}
```

### 2) دریافت وضعیت تسک

**Endpoint**

`GET /api/fertilization-recommendation/recommend/status/{task_id}/`

**Path Param**

- `task_id`: شناسه تسکی که از مرحله قبل گرفته شده

**Success Response**

```json
{
  "status": "success",
  "data": {
    "task_id": "fert-task-123",
    "status": "processing",
    "progress": {
      "message": "analyzing farm data"
    },
    "result": {
      "plan": {
        "npkRatio": "20-20-20",
        "amountPerHectare": "150 kg/ha",
        "applicationMethod": "drip",
        "applicationInterval": "every 14 days",
        "reasoning": "balanced nutrition for current growth stage"
      }
    }
  }
}
```

**Possible status values**

- `pending`
- `processing`
- `completed`
- `failed`

---

## Irrigation Recommendation

### 1) ثبت درخواست پیشنهاد

**Endpoint**

`POST /api/irrigation-recommendation/recommend/`

**Request Body**

```json
{
  "crop_id": "wheat",
  "farm_data": {
    "soilType": "loam",
    "waterQuality": "good",
    "climateZone": "semi-arid"
  },
  "soilType": "loam",
  "waterQuality": "good",
  "climateZone": "semi-arid"
}
```

**Field Description**

- `crop_id`: شناسه محصول
- `farm_data.soilType`: نوع خاک
- `farm_data.waterQuality`: کیفیت آب
- `farm_data.climateZone`: اقلیم
- `soilType`, `waterQuality`, `climateZone`: همین داده‌ها در حالت flat

**Success Response**

حالت نتیجه مستقیم:

```json
{
  "status": "success",
  "data": {
    "plan": {
      "frequencyPerWeek": "3",
      "durationMinutes": "45",
      "bestTimeOfDay": "early morning",
      "moistureLevel": "optimal",
      "warning": "avoid irrigation during strong wind"
    },
    "raw_response": "...",
    "water_balance": {
      "daily": [
        {
          "forecast_date": "2025-03-28",
          "et0_mm": 4.1,
          "etc_mm": 3.8,
          "effective_rainfall_mm": 0.0,
          "gross_irrigation_mm": 3.8,
          "irrigation_timing": "06:00"
        }
      ],
      "crop_profile": {
        "kc_initial": 0.7,
        "kc_mid": 1.05,
        "kc_end": 0.85
      },
      "active_kc": 1.05
    },
    "status": "completed"
  }
}
```

حالت async:

```json
{
  "status": "success",
  "data": {
    "task_id": "irr-task-123",
    "status": "pending"
  }
}
```

### 2) دریافت وضعیت تسک

**Endpoint**

`GET /api/irrigation-recommendation/recommend/status/{task_id}/`

**Path Param**

- `task_id`: شناسه تسک

**Success Response**

```json
{
  "status": "success",
  "data": {
    "task_id": "irr-task-123",
    "status": "completed",
    "result": {
      "plan": {
        "frequencyPerWeek": "3",
        "durationMinutes": "45",
        "bestTimeOfDay": "early morning",
        "moistureLevel": "optimal",
        "warning": "avoid irrigation during strong wind"
      },
      "raw_response": "...",
      "water_balance": {
        "daily": [],
        "crop_profile": {
          "kc_initial": 0.7,
          "kc_mid": 1.05,
          "kc_end": 0.85
        },
        "active_kc": 1.05
      },
      "status": "completed"
    }
  }
}
```

---

## پیشنهاد پیاده‌سازی در فرانت

### Fertilization

1. با `POST /recommend/` درخواست را ارسال کنید.
2. اگر `data.task_id` برگشت، polling را با `GET /recommend/status/{task_id}/` شروع کنید.
3. وقتی `data.status` به `completed` رسید، `data.result` را نمایش دهید.
4. اگر `failed` شد، پیام خطا را به کاربر نشان دهید.

### Irrigation

1. با `POST /recommend/` درخواست را ارسال کنید.
2. اگر `task_id` برگشت، هر چند ثانیه وضعیت را چک کنید.
3. وقتی `completed` شد، `result.plan` و `result.water_balance` را نمایش دهید.

## نکات

- همه پاسخ‌ها در این پروژه معمولاً با ساختار زیر برمی‌گردند:

```json
{
  "status": "success",
  "data": {}
}
```

- در صورت خطا ممکن است `status` مقدار دیگری داشته باشد یا سرویس خارجی خطای مستقیم برگرداند.
- فرانت باید هر دو حالت **direct result** و **task-based result** را هندل کند.
