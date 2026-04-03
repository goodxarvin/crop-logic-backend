
این سند قرارداد جدید endpoint پروفایل دسترسی را توضیح می‌دهد.

نکته مهم:

- فرانت فقط باید از `matched_rules` استفاده کند
- منبع حقیقت برای فرانت پاسخ API است؛ نه `access_control/apps.py`
- `subscription_plan` ممکن است از plan پیش‌فرض موثر پر شود، حتی اگر روی خود فارم قبلاً `null` بوده باشد

## 1) API پروفایل دسترسی مزرعه

- `GET /api/access-control/farms/{farm_uuid}/profile/`
- نیازمند `Authorization: Bearer <access_token>`

نمونه پاسخ:

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "farm_uuid": "11111111-1111-1111-1111-111111111111",
    "subscription_plan": {
      "uuid": "22222222-2222-2222-2222-222222222222",
      "code": "gold",
      "name": "Gold"
    },
    "matched_rules": [
      {
        "code": "gold-full-access",
        "name": "Gold Full Access",
        "effect": "allow",
        "priority": 10
      }
    ],
    "resolved_from_profile": true
  }
}
```

## 2) معنی `matched_rules`

- `matched_rules` لیست ruleهایی است که برای آن مزرعه match شده‌اند
- هر آیتم فعلاً شامل `code` و `name` و `effect` و `priority` است
- اگر ruleای match نشود، داخل این لیست نمی‌آید

## 3) رفتار پیش‌فرض plan

- plan پیش‌فرض فارم‌های جدید: `gold`
- اگر روی بعضی فارم‌های قدیمی `subscription_plan` خالی باشد، backend plan موثر پیش‌فرض را برمی‌گرداند

## 4) قرارداد جدید فرانت

- دیگر روی `features[code]` یا `groups` چیزی ننویسید
- منطق فرانت باید بر اساس `matched_rules` نوشته شود
- اگر backend بعداً شکل `matched_rules` را گسترش دهد، فرانت باید همچنان روی همین فیلد تکیه کند

## 5) گارد API

گاردهای backend همچنان بر اساس access control کار می‌کنند. اگر کاربر به APIای دسترسی نداشته باشد، پاسخ:

- `403 Forbidden`

نمونه:

```json
{
  "detail": "Access to feature `greenhouse-dashboard` is denied."
}
```
