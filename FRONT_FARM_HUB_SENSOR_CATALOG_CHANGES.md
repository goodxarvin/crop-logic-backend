# Farm Hub & Sensor Catalog Changes

این فایل برای تیم فرانت آماده شده و فقط تغییرات موثر روی قرارداد API و داده‌ها را توضیح می‌دهد.

## 1) تغییر اصلی

مدل قدیمی `plant` از جریان اصلی حذف شده و اطلاعات محصول حالا از مدل `Product` در اپ `farm_hub` خوانده می‌شود.

به همین خاطر endpoint زیر:

`/api/farm-hub/farm-types/{farm_type_uuid}/products/`

اکنون باید داده‌های هر محصول را از جدول `products` برگرداند، نه از جدول قدیمی `plant`.

## 2) endpoint های مرتبط

### لیست نوع مزرعه

`GET /api/farm-hub/farm-types/`

نمونه پاسخ:

```json
{
  "code": 200,
  "msg": "success",
  "data": [
    {
      "uuid": "farm-type-uuid",
      "name": "زراعی",
      "description": "",
      "metadata": {}
    }
  ]
}
```

### لیست محصولات بر اساس نوع مزرعه

`GET /api/farm-hub/farm-types/{farm_type_uuid}/products/`

نمونه پاسخ جدید:

```json
{
  "code": 200,
  "msg": "success",
  "data": [
    {
      "uuid": "product-uuid",
      "name": "گندم",
      "description": "",
      "metadata": {},
      "light": "",
      "watering": "",
      "soil": "لومی",
      "temperature": "",
      "planting_season": "پاییز",
      "harvest_time": "اواخر بهار",
      "spacing": "",
      "fertilizer": "",
      "health_profile": {},
      "irrigation_profile": {},
      "growth_profile": {}
    }
  ]
}
```

## 3) فیلدهای جدید هر product

قبلا فرانت فقط این‌ها را می‌گرفت:

- `uuid`
- `name`
- `description`
- `metadata`

الان این فیلدها هم اضافه شده‌اند:

- `light`
- `watering`
- `soil`
- `temperature`
- `planting_season`
- `harvest_time`
- `spacing`
- `fertilizer`
- `health_profile`
- `irrigation_profile`
- `growth_profile`

## 4) نکات مهم برای فرانت

- `health_profile`، `irrigation_profile` و `growth_profile` از نوع `JSON object` هستند
- بعضی فیلدها ممکن است رشته خالی `""` یا آبجکت خالی `{}` برگردانند
- بهتر است UI برای نبودن داده fallback داشته باشد
- مرتب‌سازی محصولات در endpoint بر اساس `name` است

## 5) سیدرهای جدید catalog

برای farm type ها و product ها سیدر گسترده‌تر اضافه شده است.

### farm type ها

- `زراعی`
- `درختی`
- `غرقابی`
- `گلخانه ای`

### محصولات seed شده

#### زراعی

- `گندم`
- `ذرت`
- `جو`
- `کلزا`
- `پنبه`

#### درختی

- `سیب`
- `پسته`
- `انگور`
- `انار`

#### غرقابی

- `برنج`

#### گلخانه ای

- `گوجه فرنگی`
- `خیار`
- `فلفل دلمه ای`

## 6) تغییرات مرتبط با farm object

در پاسخ farm، این فیلدها هم الان مهم هستند:

- `area_uuid`
- `sensors[].sensor_catalog_uuid`
- `sensors[].physical_device_uuid`

و این فیلدها از مدل حذف شده‌اند:

- `customization` در سطح farm
- `customization` در سطح sensor

## 7) sensor_catalog/apps.py

فایل:

`sensor_catalog/apps.py`

محتوا:

- اپ با نام `sensor_catalog` ثبت شده
- کلاس کانفیگ آن `SensorCatalogConfig` است
- `verbose_name` برابر `Sensor Catalog` است

نکته مهم برای فرانت:

- خود `sensor_catalog/apps.py` خروجی API را تغییر نمی‌دهد
- اثر عملی آن این است که اپ `sensor_catalog` به صورت رسمی در پروژه register شده و داده‌های سنسور حالا در `farm_hub` استفاده می‌شوند
- از این به بعد فرانت می‌تواند روی `sensor_catalog_uuid` برای سنسورها حساب کند

## 8) نتیجه نهایی برای فرانت

- منبع نمایش محصولات باید `farm_hub.products` باشد
- endpoint اصلی برای لیست محصولات هر نوع مزرعه:
  - `GET /api/farm-hub/farm-types/{farm_type_uuid}/products/`
- UI جزئیات محصول می‌تواند فیلدهای زراعی/رشد/آبیاری را مستقیم از response بخواند
- برای سنسورها باید از `sensor_catalog_uuid` و `physical_device_uuid` استفاده شود
