# مستند معماری پیشنهادی Commerce، Wallet، Order و Checkout

این سند یک طرح کامل برای اضافه کردن لایه تجارت الکترونیک و مالی به بک‌اند فعلی CropLogic ارائه می‌کند. هدف این معماری این است که:

- کاربر بتواند هم‌زمان کالاهای فیزیکی، سرویس‌ها، پلن‌های اشتراک و تجهیزات هوشمند را در یک checkout واحد خریداری کند.
- کیف پول و ledger در سطح کاربر مدیریت شود، اما سفارش‌ها و provisioning در context مزرعه انجام شود.
- WooCommerce فقط storefront و catalog/marketing باشد و منطق اصلی تجارت در بک‌اند Django نگه داشته شود.
- onboarding اولیه مزرعه، تحلیل طراحی سنسورها و تأیید کارشناسی قبل از پرداخت نهایی، به‌صورت native در backend پشتیبانی شود.
- APIهای لازم برای cart، checkout، wallet، order، payment، address و provisioning از ابتدا domain-driven طراحی شوند.

این سند هم وضعیت فعلی پروژه را بررسی می‌کند، هم appهای جدید پیشنهادی را معرفی می‌کند، هم مدل داده، APIها، workflowها، state machineها و تغییرات لازم روی appهای موجود را توضیح می‌دهد.

---

## 1) وضعیت فعلی پروژه و نکات مهم دامنه

بر اساس کد فعلی repository:

- مدل `farm_hub.models.FarmType` ساختار نوع مزرعه را نگه می‌دارد.
- مدل `farm_hub.models.Product` در حال حاضر بیشتر معادل crop/plant است، نه sellable product فروشگاهی.
- مدل `farm_hub.models.FarmHub` مالکیت مزرعه، نوع مزرعه، پلن اشتراک و محصولات کشت‌شده را نگه می‌دارد.
- مدل `subscriptions.models.SubscriptionPlan` پلن اشتراک را نگه می‌دارد.
- مدل‌های `access_control.models.AccessFeature`، `AccessRule` و `FarmAccessProfile` برای feature gating و access resolution آماده هستند.
- app `addresses` فعلاً فقط address ساده کاربر را با `province`، `city`، `postal_code` و `address_detail` نگه می‌دارد و برای سناریوی commerce کافی نیست.

نتیجه مهم:

- `farm_hub.Product` نباید به‌عنوان catalog فروشگاهی استفاده شود، چون امروز مفهوم crop/plant دارد.
- Wallet باید در سطح `User` باشد، نه `FarmHub`.
- Order باید به یک `FarmHub` مشخص reference داشته باشد، حتی اگر پرداخت از wallet کاربر انجام شود.
- Checkout اولیه مزرعه با checkoutهای عادی متفاوت است و باید workflow مستقل داشته باشد.

---

## 2) اصول معماری پیشنهادی

### اصل 1: تفکیک Catalog کشاورزی از Catalog فروش

در سیستم فعلی، `Product` در `farm_hub` معنی محصول قابل کشت دارد. برای commerce باید یک catalog مستقل برای اقلام قابل فروش ایجاد شود. این کار از تداخل مفهومی بین:

- crop product
- physical item
- subscription
- service
- installation package

جلوگیری می‌کند.

### اصل 2: تفکیک Financial Identity از Farm Context

- `Wallet`, `WalletTransaction`, `LedgerEntry`, `Refund`, `CreditBalance` به `User` متصل می‌شوند.
- `Order`, `CheckoutSession`, `SubscriptionEnrollment`, `FarmProvisionRequest`, `DeviceProvisionRequest` به `FarmHub` متصل می‌شوند.
- هر payment باید مشخص کند با چه user انجام شده و برای کدام farm مصرف شده است.

### اصل 3: WooCommerce به‌عنوان channel، نه source of truth

WooCommerce فقط برای این کارها بماند:

- نمایش storefront
- landing page و marketing
- SEO
- cart mirror در لایه نمایش
- session bridge

اما source of truth اصلی باید backend Django باشد برای:

- cart
- checkout
- pricing finalization
- discount validation
- payment state
- wallet balance
- order lifecycle
- subscription activation
- farm onboarding and provisioning

### اصل 4: Domain workflowهای طولانی باید asynchronous باشند

این موارد sync نیستند و باید با job/queue مدیریت شوند:

- تحلیل طراحی مزرعه
- پیشنهاد تعداد سنسور
- تأیید اپراتور
- provisioning مزرعه
- فعال‌سازی subscription/access profile
- ایجاد درخواست نصب در محل
- settlement و reconciliation پرداخت

### اصل 5: آدرس‌ها باید typed و reusable باشند

به‌جای یک مدل آدرس ساده، باید addressهای typed پشتیبانی شوند:

- shipping address
- farm location address
- billing/invoice address
- installation/service address

و برای هر checkout یا order snapshot شوند تا تغییرات بعدی روی آدرس، تاریخچه سفارش را خراب نکند.

---

## 3) bounded contextها و appهای پیشنهادی

در این معماری، بهتر است commerce به چند app کوچک و domain-based شکسته شود، نه یک app بزرگ.

## 3.1) appهای جدیدی که باید اضافه شوند

appهای پیشنهادی:

1. `commerce_catalog`
2. `pricing`
3. `cart`
4. `checkout`
5. `orders`
6. `payments`
7. `wallet`
8. `ledger`
9. `promotions`
10. `fulfillment`
11. `provisioning`
12. `farm_onboarding`
13. `merchant_integrations`
14. `billing`
15. `customer_profiles`

اگر بخواهید MVP سبک‌تر باشد، می‌توان نسخه اول را با این 9 app شروع کرد:

1. `commerce_catalog`
2. `cart`
3. `checkout`
4. `orders`
5. `payments`
6. `wallet`
7. `ledger`
8. `provisioning`
9. `farm_onboarding`

## 3.2) نقش هر app

### `commerce_catalog`

مسئول:

- تعریف sellable itemها
- sync با WooCommerce
- نگه‌داری SKU، نوع آیتم، قیمت پایه، tax class، نصب‌پذیری، نیاز به farm context
- مدیریت variantها، bundleها، add-onها

نباید با `farm_hub.Product` یکی شود.

### `pricing`

مسئول:

- price resolution
- campaign price
- plan upgrade/downgrade math
- installation fee
- shipping fee
- farm-analysis fee
- wallet usage policy

اگر فعلاً scope کم است می‌توان منطق آن را موقتاً داخل `checkout` نگه داشت.

### `cart`

مسئول:

- سبد خرید user
- line itemهای ترکیبی
- attach شدن line item به farm یا draft farm
- اعتبارسنجی pre-checkout
- نگه‌داری intent کاربر برای install-on-farm یا ship-only

### `checkout`

مسئول:

- checkout session چندمرحله‌ای
- جمع‌آوری آدرس‌ها
- جمع‌آوری farm setup data
- lock کردن قیمت‌ها
- ساخت payment intent
- orchestration بین cart، onboarding، payment و order

### `orders`

مسئول:

- order header
- order item
- split بین itemهای فیزیکی و سرویسی
- order status lifecycle
- snapshots نهایی قیمت، address، metadata

### `payments`

مسئول:

- payment intent
- gateway attempt
- callback
- settlement state
- reconciliation
- receipt link
- external transaction reference

### `wallet`

مسئول:

- user wallet
- available balance
- held balance
- pending settlement
- wallet top-up
- debit/credit for order payment
- refund to wallet
- wallet summary API برای dashboard و wallet page

### `ledger`

مسئول:

- double-entry bookkeeping
- financial audit trail
- debit/credit journal
- حساب‌های سیستمی مثل user_wallet، gateway_clearing، revenue، refund_reserve

`wallet` بدون `ledger` در بلندمدت برای گزارش‌گیری و audit مشکل ایجاد می‌کند.

### `promotions`

مسئول:

- coupon
- campaign
- usage rule
- farm-specific discounts
- first-onboarding incentives

### `fulfillment`

مسئول:

- shipment
- package
- delivery status
- installation appointment
- service dispatch
- inventory reservation در صورت نیاز

### `provisioning`

مسئول:

- فعال‌سازی subscription
- ساخت/به‌روزرسانی `FarmAccessProfile`
- ثبت device provisioning
- attach کردن sensor/equipment به farm
- اجرای post-payment automation

### `farm_onboarding`

مسئول:

- draft farm creation
- land map upload/reference
- block/zone input
- irrigation method
- crop selection
- async analysis
- recommendation output
- operator review
- approval gate قبل از final payment

### `merchant_integrations`

مسئول:

- bridge با WooCommerce plugin
- product sync
- customer/session sync
- webhook handling
- storefront token exchange

### `billing`

مسئول:

- invoice
- legal billing profile
- tax metadata
- accounting document number

### `customer_profiles`

مسئول:

- پروفایل تجاری/حقوقی کاربر
- national id / company id
- default shipping/billing preferences
- wallet KYC flags

---

## 4) appهای موجود که باید تغییر کنند

این بخش مهم است چون چند app فعلی باید refactor یا extend شوند.

### 4.1) `farm_hub`

تغییرات لازم:

- `FarmHub` باید بتواند با orderها، checkoutها، provisioningها و subscription enrollmentها relation داشته باشد.
- بهتر است به `FarmHub` چند فیلد domain-friendly اضافه شود:
  - `display_code`
  - `status`
  - `onboarding_status`
  - `location_point`
  - `location_geojson`
  - `farm_area_hectares`
  - `primary_address`
- `farm_hub.Product` باید در مستندات و نام‌گذاری داخلی به‌وضوح crop/plant تلقی شود، نه کالا.
- اگر امکان refactor دارید، rename مفهومی پیشنهاد می‌شود:
  - نگه‌داشتن model فعلی ولی تغییر usage documentation به `crop product`
  - یا در آینده انتقال به appی مثل `crop_catalog`

### 4.2) `subscriptions`

تغییرات لازم:

- `SubscriptionPlan` باید به sellable offering در `commerce_catalog` map شود.
- باید distinction بین:
  - plan definition
  - purchased subscription
  - activated subscription on farm
  
ایجاد شود.

پیشنهاد:

- `subscriptions` فقط plan definition را نگه دارد.
- موجودیت خریداری‌شده در `orders` یا `provisioning` ثبت شود.
- موجودیت فعال در مزرعه با مدل جدیدی مثل `FarmSubscription` نگه‌داری شود.

### 4.3) `access_control`

تغییرات لازم:

- بعد از purchase یا upgrade، باید provisioning بتواند `FarmAccessProfile` را rebuild کند.
- ruleها باید بتوانند روی plan tier و add-on feature packها هم عمل کنند.
- اگر در آینده add-onهای پولی اضافه می‌شوند، پیشنهاد می‌شود rule matching فقط به `SubscriptionPlan` محدود نباشد و entitlementهای خریداری‌شده هم دیده شوند.

### 4.4) `addresses`

این app در وضعیت فعلی برای commerce ناکافی است.

مشکلات فعلی:

- فقط یک مدل ساده `Address` دارد.
- نوع آدرس مشخص نیست.
- به farm متصل نیست.
- مختصات جغرافیایی ندارد.
- snapshot برای order ندارد.
- contact person / delivery instructions / location label ندارد.

تغییرات پیشنهادی:

- نگه‌داری `Province` و `City` خوب است و می‌تواند باقی بماند.
- مدل جدیدی مثل `AddressBookEntry` یا refactor مدل `Address` لازم است.
- باید type و usage purpose در مدل آدرس بیاید.

فیلدهای پیشنهادی:

- `uuid`
- `user`
- `farm` nullable
- `label`
- `address_type`
- `recipient_name`
- `recipient_phone`
- `province`
- `city`
- `postal_code`
- `street_address`
- `landmark`
- `latitude`
- `longitude`
- `location_point`
- `is_default`
- `is_active`
- `metadata`

enum پیشنهادی برای `address_type`:

- `shipping`
- `farm_location`
- `billing`
- `service_installation`

و برای order/checkout باید snapshot model جدا هم داشته باشید:

- `OrderAddressSnapshot`
- `CheckoutAddressSnapshot`

### 4.5) `device_hub`

تغییرات لازم:

- بعد از purchase سنسور یا دستگاه، provisioning باید بتواند device catalog را به order item وصل کند.
- installable itemها باید به `DeviceCatalog` یا تجهیز متناظر map شوند.
- اگر سنسور نیاز به serial provisioning دارد، یک مرحله post-delivery یا post-installation برای bind شدن device لازم است.

### 4.6) `dashboard`

تغییرات لازم:

- wallet summary card باید از app `wallet` داده بگیرد.
- سفارش‌های pending یا provisioning pending می‌توانند بعدها در dashboard cardهای جدید نمایش داده شوند.

---

## 5) مدل دامنه پیشنهادی

## 5.1) commerce catalog

مدل‌های اصلی:

### `SellableItem`

- `uuid`
- `code`
- `title`
- `slug`
- `item_type`
- `status`
- `description`
- `short_description`
- `base_price`
- `currency`
- `tax_class`
- `metadata`
- `requires_farm_context`
- `requires_shipping_address`
- `requires_farm_address`
- `supports_installation`
- `requires_operator_approval`
- `is_active`

enum برای `item_type`:

- `subscription_plan`
- `physical_device`
- `physical_supply`
- `service`
- `installation_service`
- `farm_analysis`
- `credit_topup`

### `SellableItemVariant`

- `uuid`
- `item`
- `sku`
- `title`
- `price_override`
- `attributes_json`
- `stock_policy`
- `is_active`

### `SellableItemRelation`

برای bundle/add-on/cross-sell:

- `parent_item`
- `child_item`
- `relation_type`

### `ExternalCatalogMapping`

- `channel`
- `external_id`
- `external_sku`
- `sellable_item`
- `payload_snapshot`
- `sync_status`

برای bridge با WooCommerce حیاتی است.

## 5.2) cart

### `Cart`

- `uuid`
- `user`
- `status`
- `currency`
- `farm` nullable
- `draft_farm_uuid` nullable
- `channel`
- `coupon_code`
- `pricing_snapshot`
- `expires_at`
- `checked_out_at`

### `CartItem`

- `uuid`
- `cart`
- `sellable_item`
- `variant`
- `item_type_snapshot`
- `title_snapshot`
- `quantity`
- `unit_price`
- `line_total`
- `target_farm` nullable
- `draft_farm_uuid` nullable
- `fulfillment_mode`
- `installation_requested`
- `shipping_address_required`
- `farm_context_required`
- `metadata`

enum برای `fulfillment_mode`:

- `ship_only`
- `install_on_farm`
- `digital_provision`
- `service_schedule`

## 5.3) farm onboarding

### `FarmOnboardingSession`

- `uuid`
- `user`
- `farm` nullable
- `status`
- `name`
- `farm_type`
- `subscription_plan`
- `map_source`
- `geojson`
- `center_lat`
- `center_lng`
- `irrigation_method_id`
- `selected_crop_ids`
- `notes`
- `analysis_requested_at`
- `analysis_completed_at`
- `approval_required`
- `approved_at`
- `approved_by`

enum `status`:

- `draft`
- `collecting_data`
- `analysis_pending`
- `analysis_running`
- `analysis_completed`
- `awaiting_operator_review`
- `approved_for_checkout`
- `rejected`
- `converted_to_farm`

### `FarmOnboardingRecommendation`

- `session`
- `summary`
- `sensor_count`
- `equipment_list_json`
- `placement_plan_json`
- `estimated_cost`
- `review_notes`

## 5.4) checkout

### `CheckoutSession`

- `uuid`
- `user`
- `cart`
- `farm` nullable
- `onboarding_session` nullable
- `status`
- `step`
- `currency`
- `pricing_snapshot`
- `shipping_address_snapshot`
- `farm_address_snapshot`
- `billing_address_snapshot`
- `customer_notes`
- `payment_deadline_at`
- `confirmed_at`

enum `status`:

- `draft`
- `awaiting_requirements`
- `awaiting_analysis`
- `awaiting_review`
- `awaiting_payment`
- `payment_processing`
- `completed`
- `cancelled`
- `expired`

## 5.5) orders

### `Order`

- `uuid`
- `order_number`
- `user`
- `farm` nullable
- `checkout_session`
- `status`
- `payment_status`
- `fulfillment_status`
- `currency`
- `subtotal_amount`
- `discount_amount`
- `shipping_amount`
- `tax_amount`
- `grand_total`
- `paid_amount`
- `wallet_paid_amount`
- `gateway_paid_amount`
- `channel`
- `metadata`

enum `status`:

- `draft`
- `placed`
- `awaiting_payment`
- `paid`
- `partially_fulfilled`
- `fulfilled`
- `cancelled`
- `refunded`
- `failed`

### `OrderItem`

- `uuid`
- `order`
- `sellable_item`
- `external_catalog_mapping` nullable
- `title_snapshot`
- `item_type`
- `quantity`
- `unit_price`
- `discount_amount`
- `line_total`
- `farm` nullable
- `shipping_requirement`
- `installation_requirement`
- `provisioning_status`
- `fulfillment_status`
- `metadata`

## 5.6) payments

### `PaymentIntent`

- `uuid`
- `user`
- `order`
- `wallet`
- `amount`
- `currency`
- `status`
- `provider`
- `provider_reference`
- `return_url`
- `callback_payload`
- `expires_at`

enum `status`:

- `draft`
- `requires_action`
- `processing`
- `authorized`
- `captured`
- `failed`
- `cancelled`
- `expired`

### `PaymentAttempt`

- `payment_intent`
- `attempt_no`
- `provider_status`
- `request_payload`
- `response_payload`
- `started_at`
- `completed_at`

## 5.7) wallet

### `Wallet`

- `uuid`
- `user`
- `status`
- `currency`
- `available_balance`
- `held_balance`
- `pending_settlement`
- `total_balance`
- `last_activity_at`

### `WalletTransaction`

- `uuid`
- `wallet`
- `transaction_type`
- `direction`
- `status`
- `amount`
- `reference_type`
- `reference_id`
- `title`
- `subtitle`
- `method`
- `created_at`
- `balance_after`
- `metadata`

enum `transaction_type`:

- `topup`
- `order_payment`
- `refund`
- `adjustment`
- `settlement`
- `withdrawal`
- `cashback`

## 5.8) ledger

### `LedgerAccount`

- `uuid`
- `code`
- `name`
- `account_type`
- `owner_user` nullable
- `owner_wallet` nullable
- `owner_farm` nullable

### `JournalEntry`

- `uuid`
- `reference_type`
- `reference_id`
- `status`
- `description`
- `occurred_at`

### `JournalLine`

- `journal_entry`
- `ledger_account`
- `debit_amount`
- `credit_amount`
- `currency`

جمع debit و credit باید برابر باشد.

## 5.9) fulfillment

### `Shipment`

- `uuid`
- `order`
- `shipping_address_snapshot`
- `status`
- `carrier`
- `tracking_number`
- `dispatch_at`
- `delivered_at`

### `InstallationRequest`

- `uuid`
- `order_item`
- `farm`
- `farm_address_snapshot`
- `status`
- `scheduled_for`
- `assigned_team`
- `notes`

## 5.10) provisioning

### `ProvisioningTask`

- `uuid`
- `order`
- `order_item`
- `farm`
- `task_type`
- `status`
- `payload`
- `result_payload`
- `error_message`
- `started_at`
- `completed_at`

enum `task_type`:

- `activate_subscription`
- `rebuild_access_profile`
- `create_farm_hub`
- `attach_devices`
- `create_service_ticket`
- `issue_refund`

---

## 6) تفکیک addressها در سناریوهای مختلف

در این پروژه address فقط یک مفهوم UI نیست؛ domain behavior دارد.

### 6.1) shipping address

برای:

- سنسور
- تجهیزات
- کود
- بذر
- سایر کالاهای فیزیکی

فیلدهای مهم:

- گیرنده
- شماره تماس
- آدرس پستی
- کدپستی
- توضیحات تحویل

### 6.2) farm location address

برای:

- ایجاد `FarmHub`
- نصب سنسور
- سرویس حضوری
- محاسبه طراحی سنسور
- نقشه و geospatial processing

فیلدهای مهم:

- مختصات دقیق
- GeoJSON یا polygon مزرعه
- نام مزرعه
- توضیحات دسترسی
- نوع زمین

### 6.3) billing address

برای:

- فاکتور رسمی
- صورتحساب حقوقی
- tax document

### 6.4) service installation address

در بعضی موارد با farm location یکی است، ولی همیشه نه. مثلا:

- تجهیزات به منزل یا انبار ارسال شود
- بعداً برای نصب به محل مزرعه منتقل شود

پس باید UI و backend اجازه دهند:

- shipping address != farm location
- shipping address == farm location
- service installation address == farm location
- service installation address جداگانه تعریف شود

### 6.5) پیشنهاد API برای addresses

مسیرهای پیشنهادی:

- `GET /api/addresses/`
- `POST /api/addresses/`
- `PATCH /api/addresses/{uuid}/`
- `GET /api/addresses/types/`
- `POST /api/checkout/{uuid}/addresses/shipping/`
- `POST /api/checkout/{uuid}/addresses/farm-location/`
- `POST /api/checkout/{uuid}/addresses/billing/`

### 6.6) تغییر پیشنهادی روی app فعلی `addresses`

حداقل تغییرات:

- rename منطقی endpointها از `api/address/` به `api/addresses/`
- افزودن `uuid`
- افزودن `label`
- افزودن `address_type`
- افزودن `recipient_name`
- افزودن `recipient_phone`
- افزودن `latitude`
- افزودن `longitude`
- افزودن `farm` nullable
- افزودن `metadata`
- افزودن فیلدهای default و active

### 6.7) تغییرات دقیق پیشنهادی در مدل `addresses`

پیشنهاد می‌شود app فعلی `addresses` از یک address book ساده به یک address domain کامل ارتقا پیدا کند.

#### ساختار پیشنهادی مدل اصلی

به‌جای مدل فعلی `Address` با فیلدهای محدود، این ساختار پیشنهاد می‌شود:

- `uuid`
- `user`
- `farm` nullable
- `label`
- `address_type`
- `recipient_name`
- `recipient_phone`
- `province`
- `city`
- `postal_code`
- `street_address`
- `address_detail`
- `landmark`
- `latitude`
- `longitude`
- `location_point`
- `delivery_instructions`
- `is_default`
- `is_active`
- `metadata`
- `created_at`
- `updated_at`

#### تغییرات روی مدل‌های موجود

- مدل `Province` و `City` می‌توانند باقی بمانند.
- بهتر است `related_name`های فعلی در `Address` بازبینی شوند چون الان `province` و `city` برای relation naming مناسب commerce نیستند.
- بهتر است برای `Address` از `UUIDField` استفاده شود تا در APIها `pk` عددی expose نشود.
- فیلد `address_detail` بهتر است حفظ شود اما `street_address` هم جدا اضافه شود تا UI بتواند آدرس ساختاریافته‌تری ارسال کند.

#### مدل snapshot برای checkout و order

برای جلوگیری از تغییر تاریخچه:

- `CheckoutAddressSnapshot`
- `OrderAddressSnapshot`

هر snapshot باید حداقل این فیلدها را نگه دارد:

- `source_address_uuid` nullable
- `address_type`
- `label`
- `recipient_name`
- `recipient_phone`
- `province_name`
- `city_name`
- `postal_code`
- `street_address`
- `address_detail`
- `latitude`
- `longitude`
- `location_geojson`
- `delivery_instructions`

#### ruleهای validation آدرس

- `shipping` باید `recipient_name` و `recipient_phone` داشته باشد.
- `farm_location` باید حداقل یا مختصات داشته باشد یا geojson/location payload معتبر.
- `billing` می‌تواند برای شخص حقیقی یا حقوقی metadata مجزا داشته باشد.
- اگر `installation_requested=true` باشد و item نصب‌پذیر باشد، وجود `farm_location` الزامی است.
- اگر order فقط digital/subscription باشد، shipping address لازم نیست.

#### migration strategy برای `addresses`

1. افزودن `uuid` و فیلدهای جدید به مدل فعلی
2. migration داده برای map کردن `address_detail` به `street_address/address_detail`
3. افزودن enum برای `address_type`
4. افزودن relation اختیاری به `FarmHub`
5. افزودن endpointهای جدید
6. نگه‌داشتن endpoint قبلی `api/address/` به‌صورت deprecated برای مدت کوتاه

### 6.8) APIهای user-facing برای `addresses`

- `GET /api/addresses/`
- `POST /api/addresses/`
- `GET /api/addresses/{uuid}/`
- `PATCH /api/addresses/{uuid}/`
- `DELETE /api/addresses/{uuid}/`
- `POST /api/addresses/{uuid}/set-default/`
- `GET /api/addresses/types/`
- `GET /api/addresses/provinces/`
- `GET /api/addresses/provinces/{provinceId}/cities/`

نمونه payload پیشنهادی:

```json
{
  "label": "مزرعه اصلی",
  "addressType": "farm_location",
  "recipientName": "علی رضایی",
  "recipientPhone": "09120000000",
  "provinceId": 1,
  "cityId": 12,
  "postalCode": "1234567890",
  "streetAddress": "جاده قدیم، بعد از پل",
  "addressDetail": "ورودی دوم، کنار انبار",
  "latitude": 35.123,
  "longitude": 51.456,
  "deliveryInstructions": "قبل از مراجعه تماس بگیرید",
  "farmUuid": null
}
```

### 6.9) APIهای admin/backoffice برای `addresses`

برای پنل admin، آدرس فقط CRUD ساده نیست؛ باید ابزار پشتیبانی و بررسی order را هم بدهد.

- `GET /api/admin/addresses/`
- `GET /api/admin/addresses/{uuid}/`
- `PATCH /api/admin/addresses/{uuid}/`
- `GET /api/admin/addresses/?userId=`
- `GET /api/admin/addresses/?farmUuid=`
- `GET /api/admin/addresses/?addressType=shipping`
- `GET /api/admin/orders/{orderUuid}/addresses/`
- `GET /api/admin/checkout/sessions/{checkoutUuid}/addresses/`

کاربرد admin:

- مشاهده آدرس‌های ثبت‌شده کاربر
- بررسی آدرس snapshot شده روی order
- اصلاح آدرس قبل از dispatch
- بررسی اینکه shipping address و farm location یکی هستند یا نه
- تشخیص اینکه سفارش نیاز به نصب در مزرعه دارد یا فقط ارسال

---

## 7) سناریوهای اصلی کسب‌وکار

## 7.1) خرید عادی کالا

مثال:

- کاربر کود یا بذر یا تجهیزات ساده می‌خرد.

workflow:

1. user item را به cart اضافه می‌کند.
2. backend چک می‌کند item فقط shipping address می‌خواهد یا نه.
3. checkout shipping address را می‌گیرد.
4. pricing finalization انجام می‌شود.
5. payment intent ساخته می‌شود.
6. پس از پرداخت موفق، order ثبت می‌شود.
7. shipment/fulfillment آغاز می‌شود.

## 7.2) خرید subscription برای مزرعه موجود

workflow:

1. user farm موردنظر را انتخاب می‌کند.
2. plan به cart اضافه می‌شود.
3. checkout farm context را validate می‌کند.
4. payment انجام می‌شود.
5. provisioning task برای activate subscription ساخته می‌شود.
6. `FarmAccessProfile` rebuild می‌شود.

## 7.3) خرید سنسور با نصب روی مزرعه

workflow:

1. user item را با `installation_requested=true` به cart اضافه می‌کند.
2. farm و farm location مشخص می‌شود.
3. shipping address و farm address می‌تواند یکسان یا متفاوت باشد.
4. بعد از پرداخت:
   - order item ساخته می‌شود
   - installation request ساخته می‌شود
   - پس از نصب، provisioning نهایی انجام می‌شود

## 7.4) onboarding اولیه مزرعه + طراحی سنسور + پرداخت

این سناریو مهم‌ترین workflow اختصاصی شما است.

workflow پیشنهادی:

1. user از storefront یا اپ، flow ایجاد مزرعه جدید را شروع می‌کند.
2. `FarmOnboardingSession` ساخته می‌شود.
3. اطلاعات اولیه جمع می‌شود:
   - نام مزرعه
   - نوع مزرعه
   - نقشه و مختصات
   - بلوک‌ها
   - محصولات مورد کشت
   - روش آبیاری
4. اگر cart شامل subscription یا تجهیز هوشمند وابسته به farm باشد، checkout به onboarding session وصل می‌شود.
5. تحلیل طراحی مزرعه async شروع می‌شود.
6. نتیجه شامل تعداد سنسور، محل استقرار و تجهیزات پیشنهادی تولید می‌شود.
7. در صورت نیاز، وضعیت به `awaiting_operator_review` می‌رود.
8. اپراتور نتیجه را approve/reject می‌کند.
9. پس از approve، checkout به `awaiting_payment` می‌رود.
10. user payment نهایی را انجام می‌دهد.
11. پس از موفقیت:
    - `FarmHub` نهایی ساخته یا draft آن finalize می‌شود
    - order ثبت می‌شود
    - subscription و entitlementها فعال می‌شوند
    - installation/fulfillment taskها ایجاد می‌شوند

این flow نباید فقط با `Order` ساده مدل شود. باید `FarmOnboardingSession` و `CheckoutSession` مستقل داشته باشد.

---

## 8) state machineهای پیشنهادی

## 8.1) cart state

- `active`
- `locked`
- `converted`
- `abandoned`
- `expired`

## 8.2) checkout state

- `draft`
- `awaiting_requirements`
- `awaiting_analysis`
- `awaiting_review`
- `awaiting_payment`
- `payment_processing`
- `completed`
- `cancelled`
- `expired`

## 8.3) order state

- `placed`
- `paid`
- `processing`
- `partially_fulfilled`
- `fulfilled`
- `cancelled`
- `refunded`
- `failed`

## 8.4) payment state

- `draft`
- `processing`
- `authorized`
- `captured`
- `failed`
- `cancelled`
- `expired`

## 8.5) wallet transaction state

- `pending`
- `posted`
- `failed`
- `reversed`

## 8.6) onboarding state

- `draft`
- `collecting_data`
- `analysis_pending`
- `analysis_running`
- `analysis_completed`
- `awaiting_operator_review`
- `approved_for_checkout`
- `rejected`
- `converted_to_farm`

---

## 9) API architecture پیشنهادی

پیشنهاد می‌شود همه endpointها زیر namespace جدید commerce قرار نگیرند؛ بهتر است domain-based بمانند ولی prefix یکدست داشته باشند.

نمونه:

- `api/commerce/catalog/...`
- `api/cart/...`
- `api/checkout/...`
- `api/orders/...`
- `api/payments/...`
- `api/wallet/...`
- `api/ledger/...`
- `api/addresses/...`
- `api/farm-onboarding/...`
- `api/merchant-integrations/...`

---

## 10) APIهای پیشنهادی برای هر app

## 10.1) `commerce_catalog`

### Catalog browsing

- `GET /api/commerce/catalog/items/`
- `GET /api/commerce/catalog/items/{uuid}/`
- `GET /api/commerce/catalog/items/?itemType=physical_device`
- `GET /api/commerce/catalog/items/?requiresFarmContext=true`
- `GET /api/commerce/catalog/variants/{uuid}/`

### Sync/admin

- `POST /api/merchant-integrations/woocommerce/sync/products/`
- `POST /api/merchant-integrations/woocommerce/webhooks/product-updated/`

نمونه response:

```json
{
  "items": [
    {
      "uuid": "f0b3d8a0-8b5d-4a5f-a8ab-1f2f82b6ce17",
      "code": "sensor-soil-7in1",
      "title": "سنسور 7 کاره خاک",
      "itemType": "physical_device",
      "basePrice": 185000000,
      "currency": "IRR",
      "requiresFarmContext": true,
      "requiresShippingAddress": true,
      "requiresFarmAddress": false,
      "supportsInstallation": true
    }
  ]
}
```

## 10.2) `cart`

### Cart management

- `GET /api/cart/active/`
- `POST /api/cart/items/`
- `PATCH /api/cart/items/{uuid}/`
- `DELETE /api/cart/items/{uuid}/`
- `POST /api/cart/apply-coupon/`
- `POST /api/cart/assign-farm/`
- `POST /api/cart/validate/`

نمونه add item:

```json
{
  "sellableItemUuid": "f0b3d8a0-8b5d-4a5f-a8ab-1f2f82b6ce17",
  "quantity": 2,
  "fulfillmentMode": "install_on_farm",
  "installationRequested": true,
  "farmUuid": "optional-existing-farm-uuid",
  "draftFarmUuid": "optional-onboarding-session-uuid"
}
```

## 10.3) `farm_onboarding`

### Draft creation and analysis

- `POST /api/farm-onboarding/sessions/`
- `GET /api/farm-onboarding/sessions/{uuid}/`
- `PATCH /api/farm-onboarding/sessions/{uuid}/`
- `POST /api/farm-onboarding/sessions/{uuid}/map/`
- `POST /api/farm-onboarding/sessions/{uuid}/blocks/`
- `POST /api/farm-onboarding/sessions/{uuid}/run-analysis/`
- `GET /api/farm-onboarding/sessions/{uuid}/status/`
- `GET /api/farm-onboarding/sessions/{uuid}/recommendation/`
- `POST /api/farm-onboarding/sessions/{uuid}/approve/`
- `POST /api/farm-onboarding/sessions/{uuid}/reject/`

## 10.4) `checkout`

### Session orchestration

- `POST /api/checkout/sessions/`
- `GET /api/checkout/sessions/{uuid}/`
- `PATCH /api/checkout/sessions/{uuid}/`
- `POST /api/checkout/sessions/{uuid}/attach-onboarding/`
- `POST /api/checkout/sessions/{uuid}/addresses/shipping/`
- `POST /api/checkout/sessions/{uuid}/addresses/farm-location/`
- `POST /api/checkout/sessions/{uuid}/addresses/billing/`
- `POST /api/checkout/sessions/{uuid}/pricing/refresh/`
- `POST /api/checkout/sessions/{uuid}/confirm/`

نمونه response:

```json
{
  "uuid": "2e95bfe3-17ce-4f95-a098-8d2b7eeb33f6",
  "status": "awaiting_payment",
  "step": "payment",
  "requirements": {
    "needsShippingAddress": true,
    "needsFarmLocation": true,
    "needsBillingAddress": false,
    "needsOnboardingApproval": true
  },
  "pricing": {
    "subtotal": 248500000,
    "discount": 0,
    "shipping": 12000000,
    "grandTotal": 260500000
  }
}
```

## 10.5) `payments`

- `POST /api/payments/intents/`
- `GET /api/payments/intents/{uuid}/`
- `POST /api/payments/intents/{uuid}/pay-with-wallet/`
- `POST /api/payments/intents/{uuid}/pay-with-gateway/`
- `POST /api/payments/callback/{provider}/`
- `GET /api/payments/intents/{uuid}/receipt/`

### ترکیب پرداخت پیشنهادی

بهتر است payment engine از ابتدا hybrid payment را پشتیبانی کند:

- full wallet payment
- full gateway payment
- partial wallet + partial gateway

## 10.6) `orders`

- `GET /api/orders/`
- `GET /api/orders/{uuid}/`
- `GET /api/orders/{uuid}/items/`
- `POST /api/orders/{uuid}/cancel/`
- `POST /api/orders/{uuid}/request-refund/`
- `GET /api/orders/{uuid}/timeline/`

### Query params مهم

- `farmUuid`
- `status`
- `paymentStatus`
- `from`
- `to`
- `search`
- `page`
- `pageSize`

## 10.7) `wallet`

این بخش باید نیاز UI فعلی شما را مستقیم پوشش دهد.

### Summary endpoints

- `GET /api/wallet/summary/`
- `GET /api/wallet/accounts/`
- `GET /api/wallet/transactions/`
- `GET /api/wallet/transactions/{id}/`
- `GET /api/wallet/transactions/{id}/receipt/`

### Wallet actions

- `POST /api/wallet/topups/`
- `POST /api/wallet/withdrawals/`
- `POST /api/wallet/transfers/` در صورت نیاز آینده

### response پیشنهادی برای summary

```json
{
  "walletStatusLabel": "کیف پول عملیاتی فعال",
  "walletTitle": "کیف پول مزرعه",
  "walletDescription": "مدیریت جریان نقدی، واریزها، برداشت ها و تسویه ها",
  "balance": 248500000,
  "availableToWithdraw": 176900000,
  "pendingSettlement": 12400000,
  "monthlyInflow": 94800000,
  "monthlyOutflow": 51200000,
  "averageSettlementTimeHours": 18,
  "successfulTransactionsRate": 92,
  "healthLabel": "جریان نقدی پایدار",
  "lastUpdatedAt": "2025-02-20T10:30:00Z",
  "insights": [
    {
      "label": "نرخ موفقیت تراکنش ها",
      "value": "92%",
      "progress": 92,
      "color": "success"
    }
  ],
  "stats": [
    {
      "id": "available_to_withdraw",
      "title": "موجودی قابل برداشت",
      "value": 176900000,
      "icon": "tabler-wallet",
      "color": "success"
    }
  ]
}
```

### response پیشنهادی برای transactions

```json
{
  "items": [
    {
      "id": "TXN-9012",
      "title": "فروش محصول گندم",
      "subtitle": "تسویه بازارچه مرکزی",
      "category": "واریز",
      "amount": 18700000,
      "status": "موفق",
      "method": "انتقال پایا",
      "createdAt": "2025-02-20T08:30:00Z",
      "createdAtLabel": "۲ اسفند ۱۴۰۳ - ۰۸:۳۰",
      "balanceAfter": 248500000,
      "icon": "tabler-wheat",
      "iconColor": "success"
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "totalItems": 120,
    "totalPages": 6
  },
  "summary": {
    "balance": 248500000,
    "pendingSettlement": 12400000
  }
}
```

### Query params برای transactions

- `farmUuid` optional
- `page`
- `pageSize`
- `category`
- `status`
- `search`
- `sortBy`
- `sortOrder`
- `from`
- `to`

نکته:

- چون wallet در سطح user است، `farmUuid` باید optional filter باشد، نه owner scope اصلی.

## 10.8) `fulfillment`

- `GET /api/fulfillment/shipments/`
- `GET /api/fulfillment/shipments/{uuid}/`
- `GET /api/fulfillment/installations/`
- `POST /api/fulfillment/installations/{uuid}/schedule/`
- `POST /api/fulfillment/installations/{uuid}/complete/`

## 10.9) `provisioning`

- `GET /api/provisioning/tasks/`
- `GET /api/provisioning/tasks/{uuid}/`
- `POST /api/provisioning/tasks/{uuid}/retry/`

این API بیشتر admin/internal خواهد بود.

## 10.10) APIهای موردنیاز برای پنل admin / backoffice

پیشنهاد می‌شود APIهای پنل admin از APIهای user-facing جدا باشند تا:

- permissionها واضح‌تر شوند
- query/filterهای سنگین وارد API کاربر نشوند
- عملیات حساس مثل refund، override، retry و manual approval کنترل‌شده باشند
- audit trail برای عملیات اپراتوری بهتر ثبت شود

پیشنهاد namespace:

- `api/admin/catalog/...`
- `api/admin/orders/...`
- `api/admin/payments/...`
- `api/admin/wallet/...`
- `api/admin/checkout/...`
- `api/admin/farm-onboarding/...`
- `api/admin/provisioning/...`
- `api/admin/addresses/...`

### A) Admin Catalog APIs

- `GET /api/admin/catalog/items/`
- `POST /api/admin/catalog/items/`
- `GET /api/admin/catalog/items/{uuid}/`
- `PATCH /api/admin/catalog/items/{uuid}/`
- `POST /api/admin/catalog/items/{uuid}/activate/`
- `POST /api/admin/catalog/items/{uuid}/deactivate/`
- `GET /api/admin/catalog/mappings/woocommerce/`
- `POST /api/admin/catalog/mappings/woocommerce/sync/`

کاربرد:

- مدیریت sellable itemها
- فعال/غیرفعال کردن item
- کنترل mapping با WooCommerce
- بررسی sync status و payloadها

### B) Admin Cart and Checkout APIs

- `GET /api/admin/cart/`
- `GET /api/admin/cart/{uuid}/`
- `GET /api/admin/checkout/sessions/`
- `GET /api/admin/checkout/sessions/{uuid}/`
- `POST /api/admin/checkout/sessions/{uuid}/force-expire/`
- `POST /api/admin/checkout/sessions/{uuid}/force-cancel/`
- `POST /api/admin/checkout/sessions/{uuid}/recalculate-pricing/`

کاربرد:

- پشتیبانی checkoutهای stuck
- بررسی requirementهای ناقص
- expire/cancel دستی session
- refresh pricing در موارد استثنایی

### C) Admin Farm Onboarding APIs

- `GET /api/admin/farm-onboarding/sessions/`
- `GET /api/admin/farm-onboarding/sessions/{uuid}/`
- `GET /api/admin/farm-onboarding/sessions/?status=awaiting_operator_review`
- `POST /api/admin/farm-onboarding/sessions/{uuid}/approve/`
- `POST /api/admin/farm-onboarding/sessions/{uuid}/reject/`
- `POST /api/admin/farm-onboarding/sessions/{uuid}/rerun-analysis/`
- `POST /api/admin/farm-onboarding/sessions/{uuid}/override-recommendation/`

کاربرد:

- صف review کارشناسی
- تأیید یا رد طراحی مزرعه
- اجرای مجدد تحلیل
- override پیشنهاد سنسورها و تجهیزات

### D) Admin Order APIs

- `GET /api/admin/orders/`
- `GET /api/admin/orders/{uuid}/`
- `GET /api/admin/orders/{uuid}/timeline/`
- `GET /api/admin/orders/{uuid}/items/`
- `POST /api/admin/orders/{uuid}/mark-paid/`
- `POST /api/admin/orders/{uuid}/cancel/`
- `POST /api/admin/orders/{uuid}/refund/`
- `POST /api/admin/orders/{uuid}/split/`
- `POST /api/admin/orders/{uuid}/resend-notification/`

query params مهم:

- `status`
- `paymentStatus`
- `fulfillmentStatus`
- `farmUuid`
- `userId`
- `orderNumber`
- `from`
- `to`

کاربرد:

- جست‌وجوی orderها
- refund یا cancel توسط اپراتور
- بررسی history و breakdown itemها
- split order در caseهای خاص

### E) Admin Payment APIs

- `GET /api/admin/payments/intents/`
- `GET /api/admin/payments/intents/{uuid}/`
- `GET /api/admin/payments/intents/{uuid}/attempts/`
- `POST /api/admin/payments/intents/{uuid}/retry/`
- `POST /api/admin/payments/intents/{uuid}/mark-failed/`
- `POST /api/admin/payments/intents/{uuid}/reconcile/`
- `GET /api/admin/payments/provider-callback-logs/`

کاربرد:

- بررسی paymentهای ناموفق
- مشاهده callback payload
- retry یا reconcile دستی
- کنترل payment drift با gateway

### F) Admin Wallet APIs

- `GET /api/admin/wallets/`
- `GET /api/admin/wallets/{uuid}/`
- `GET /api/admin/wallets/{uuid}/transactions/`
- `POST /api/admin/wallets/{uuid}/adjust-balance/`
- `POST /api/admin/wallets/{uuid}/hold/`
- `POST /api/admin/wallets/{uuid}/release-hold/`
- `POST /api/admin/wallets/{uuid}/manual-refund/`
- `GET /api/admin/wallets/reports/summary/`

کاربرد:

- پشتیبانی مالی
- adjustment کنترل‌شده
- hold/release برای بررسی تقلب یا اختلاف
- گزارش‌گیری مالی پنل

نکته مهم:

- `adjust-balance` باید حتماً reason code، note و audit actor داشته باشد.

### G) Admin Fulfillment APIs

- `GET /api/admin/fulfillment/shipments/`
- `GET /api/admin/fulfillment/shipments/{uuid}/`
- `POST /api/admin/fulfillment/shipments/{uuid}/dispatch/`
- `POST /api/admin/fulfillment/shipments/{uuid}/mark-delivered/`
- `GET /api/admin/fulfillment/installations/`
- `POST /api/admin/fulfillment/installations/{uuid}/schedule/`
- `POST /api/admin/fulfillment/installations/{uuid}/assign-team/`
- `POST /api/admin/fulfillment/installations/{uuid}/complete/`

کاربرد:

- مدیریت ارسال و نصب
- تعیین تیم عملیات
- ثبت completion واقعی در مزرعه

### H) Admin Provisioning APIs

- `GET /api/admin/provisioning/tasks/`
- `GET /api/admin/provisioning/tasks/{uuid}/`
- `POST /api/admin/provisioning/tasks/{uuid}/retry/`
- `POST /api/admin/provisioning/tasks/{uuid}/force-complete/`
- `POST /api/admin/provisioning/tasks/{uuid}/mark-failed/`

کاربرد:

- پیگیری taskهای async
- retry after failure
- بررسی dependencyهای subscription/access/device attach

### I) Admin Address APIs

- `GET /api/admin/addresses/`
- `GET /api/admin/addresses/{uuid}/`
- `PATCH /api/admin/addresses/{uuid}/`
- `GET /api/admin/orders/{orderUuid}/addresses/`
- `GET /api/admin/checkout/sessions/{checkoutUuid}/addresses/`

این بخش در سناریوهای dispatch و پشتیبانی order بسیار مهم است.

### J) Admin Analytics and Ops APIs

- `GET /api/admin/commerce/metrics/overview/`
- `GET /api/admin/commerce/metrics/orders/`
- `GET /api/admin/commerce/metrics/payments/`
- `GET /api/admin/commerce/metrics/wallet/`
- `GET /api/admin/commerce/metrics/onboarding/`

نمونه KPIها:

- conversion rate checkout
- payment success rate
- average settlement time
- pending provisioning count
- awaiting operator review count
- shipment delay count

### K) Permissionهای پنل admin

پیشنهاد می‌شود roleهای زیر تعریف شوند:

- `commerce_admin`
- `finance_admin`
- `support_agent`
- `fulfillment_operator`
- `agronomy_reviewer`
- `catalog_manager`

نمونه محدودسازی:

- `finance_admin` به wallet adjustment و refund دسترسی دارد.
- `support_agent` فقط read و note/add tracking دارد.
- `agronomy_reviewer` فقط onboarding review و recommendation approval دارد.
- `catalog_manager` فقط catalog و Woo mapping را مدیریت می‌کند.

---

## 11) ارتباط WooCommerce با backend

چون ووکامرس source of truth نیست، معماری integration باید روشن باشد.

### 11.1) نقش پلاگین وردپرس

پلاگین bridge باید:

- user session را با backend sync کند.
- catalog را از backend یا mapping داخلی بخواند.
- cart changes را به backend push کند.
- checkout session id را نگه دارد.
- user را به صفحه‌های multi-step checkout هدایت کند.
- webhookهای تغییر order/payment سطح storefront را فقط mirror کند، نه authoritative.

### 11.2) data flow پیشنهادی

1. محصول در Woo نمایش داده می‌شود.
2. Woo plugin با `external_id` یا `sku` آن را به `SellableItem` map می‌کند.
3. add-to-cart در backend ثبت می‌شود.
4. checkout در backend پیش می‌رود.
5. نتیجه پرداخت و order نهایی در backend ثبت می‌شود.
6. در صورت نیاز، Woo فقط order mirror یا display record دریافت می‌کند.

### 11.3) نکته مهم

بهتر است order اصلی در Woo ساخته نشود یا اگر ساخته می‌شود، shadow order باشد.

یعنی:

- authoritative order id = backend
- Woo order id = optional channel mirror

---

## 12) منطق wallet و ledger

## 12.1) چرا `wallet` و `ledger` را جدا کنیم

`wallet` برای product/API مناسب است، ولی `ledger` برای audit و accounting.

مثلاً وقتی user با کیف پول سفارش پرداخت می‌کند:

- `Wallet.available_balance` کم می‌شود
- `WalletTransaction` ثبت می‌شود
- هم‌زمان در `ledger` باید journal entry زده شود:
  - debit: user wallet liability
  - credit: order clearing / revenue holding

### مزیت

- گزارش‌گیری مالی درست
- امکان rollback/refund امن
- traceability
- settlement با gateway و حسابداری داخلی

## 12.2) accountهای نمونه در ledger

- `wallet:user:{user_id}`
- `gateway_clearing:{provider}`
- `customer_refund_reserve`
- `sales_revenue`
- `shipping_revenue`
- `tax_payable`
- `promo_expense`

## 12.3) pending settlement

برای UI wallet باید تعریف دقیق داشته باشد. پیشنهاد:

- `pendingSettlement` = مبلغی که تراکنش مالی آن ثبت شده ولی هنوز withdrawable/settled نیست.

مثال:

- top-up کارت به کیف پول که هنوز settlement بانکی آن قطعی نشده
- refund در حال پردازش
- درآمدی که هنوز دوره تسویه آن کامل نشده

این تعریف باید در business rule صریح شود.

---

## 13) order و payment ownership

چون user می‌تواند چند مزرعه داشته باشد، هر موجودیت باید owner و context مشخص داشته باشد.

### پیشنهاد ownership

- `Wallet.user` = owner
- `Cart.user` = owner
- `CheckoutSession.user` = owner
- `Order.user` = payer/customer
- `Order.farm` = target operating farm
- `PaymentIntent.user` = payer
- `PaymentIntent.order` = commercial subject
- `ProvisioningTask.farm` = operational target

### قانون مهم

اگر cart شامل آیتم‌های متعلق به چند مزرعه باشد، دو انتخاب دارید:

1. در MVP اجازه ندهید یک order برای چند farm ساخته شود.
2. یا split order per farm انجام دهید.

پیشنهاد عملی برای MVP:

- هر checkout فقط یک `farm context` داشته باشد.
- اگر user برای چند مزرعه خرید می‌کند، cart را در checkout به چند order split کنید.

---

## 14) constraints و ruleهای مهم business

### 14.1) ruleهای item

هر `SellableItem` باید flagهای رفتاری داشته باشد:

- آیا farm لازم دارد؟
- آیا shipping address لازم دارد؟
- آیا farm location لازم دارد؟
- آیا installation پشتیبانی می‌کند؟
- آیا operator approval لازم دارد؟

### 14.2) ruleهای cart

- اگر item از نوع subscription باشد، farm context لازم است.
- اگر item از نوع physical_supply باشد، فقط shipping address کافی است.
- اگر item از نوع physical_device باشد و `installation_requested=true`، farm location لازم است.
- اگر item از نوع service باشد، ممکن است service address یا farm لازم باشد.
- اگر onboarding analysis pending باشد، checkout نباید به payment برود.

### 14.3) ruleهای payment

- order نباید قبل از price freeze پرداخت شود.
- order paid نباید دوباره capture شود.
- refund نباید از paid amount بیشتر شود.

### 14.4) ruleهای provisioning

- subscription فقط بعد از payment success فعال شود.
- access profile فقط بعد از activation/update entitlement rebuild شود.
- device attach فقط بعد از fulfillment/install complete انجام شود مگر در حالت pre-provisioning.

---

## 15) پیشنهاد endpointهای wallet متناسب با UI فعلی

برای UI موجودی که در درخواست شما آمده، این قرارداد از همه مناسب‌تر است:

### `GET /api/wallet/summary/`

خروجی:

- dashboard summary card
- hero section
- stat cards
- insights

### `GET /api/wallet/accounts/`

خروجی:

- linked accounts

### `GET /api/wallet/transactions/`

خروجی:

- transaction table paginated

### `GET /api/wallet/transactions/{id}/`

خروجی:

- detail
- tracking status
- failure reason
- settlement eta

### `GET /api/wallet/transactions/{id}/receipt/`

خروجی:

- file یا redirect URL

این split با نیاز UI فعلی هماهنگ است و سریع هم لود می‌شود.

---

## 16) تغییرات پیشنهادی در `config/urls.py`

بعد از اضافه شدن appها، routing پیشنهادی:

```python
urlpatterns += [
    path("api/commerce/catalog/", include("commerce_catalog.urls")),
    path("api/cart/", include("cart.urls")),
    path("api/checkout/", include("checkout.urls")),
    path("api/orders/", include("orders.urls")),
    path("api/payments/", include("payments.urls")),
    path("api/wallet/", include("wallet.urls")),
    path("api/ledger/", include("ledger.urls")),
    path("api/farm-onboarding/", include("farm_onboarding.urls")),
    path("api/fulfillment/", include("fulfillment.urls")),
    path("api/provisioning/", include("provisioning.urls")),
    path("api/promotions/", include("promotions.urls")),
    path("api/merchant-integrations/", include("merchant_integrations.urls")),
    path("api/billing/", include("billing.urls")),
    path("api/addresses/", include("addresses.urls")),
]
```

نکته:

- بهتر است مسیر فعلی `api/address/` به `api/addresses/` تغییر کند.
- برای backward compatibility می‌توانید مدتی هر دو را نگه دارید.

---

## 17) پیشنهاد service layer داخلی

برای جلوگیری از چاق شدن viewها، بهتر است از ابتدا service module داشته باشید.

نمونه:

- `commerce_catalog/services.py`
- `cart/services.py`
- `checkout/services.py`
- `orders/services.py`
- `payments/services.py`
- `wallet/services.py`
- `ledger/services.py`
- `provisioning/services.py`
- `farm_onboarding/services.py`

serviceهای کلیدی:

- `CartService`
- `CheckoutRequirementService`
- `CheckoutPricingService`
- `PaymentOrchestrator`
- `OrderCreationService`
- `WalletPostingService`
- `LedgerPostingService`
- `FarmOnboardingAnalysisService`
- `ProvisioningOrchestrator`
- `WooCommerceSyncService`

---

## 18) asynchronous jobها و Celery taskها

این سیستم بدون task queue کامل نمی‌شود.

taskهای پیشنهادی:

- `run_farm_onboarding_analysis`
- `request_operator_review`
- `sync_woocommerce_products`
- `reconcile_payment_provider`
- `post_wallet_settlement`
- `create_order_fulfillment_tasks`
- `activate_farm_subscription`
- `rebuild_farm_access_profile`
- `generate_receipt_pdf`
- `send_order_notifications`

status tracking برای taskهای طولانی باید در model ذخیره شود، نه فقط در log.

---

## 19) پیشنهاد notification hookها

اتصال با app فعلی `notifications`:

- cart reminder
- checkout awaiting payment
- payment success/failure
- onboarding analysis completed
- operator approved design
- order shipped
- installation scheduled
- refund completed

---

## 20) امنیت، permission و audit

### 20.1) security

- wallet APIs همیشه user-scoped باشند.
- order APIs فقط orderهای owner را برگردانند.
- farm-scoped orderها باید ownership user نسبت به farm را validate کنند.
- callback payment provider باید signature verification داشته باشد.
- receipt URLها باید signed یا short-lived باشند.

### 20.2) audit

برای این modelها audit trail حیاتی است:

- `Order`
- `PaymentIntent`
- `WalletTransaction`
- `JournalEntry`
- `FarmOnboardingSession`
- `ProvisioningTask`

حداقل باید این موارد log شوند:

- actor
- action
- before/after status
- timestamp
- request id

---

## 21) MVP پیشنهادی

اگر بخواهید سریع UI فعلی را unblock کنید و بعد گسترش دهید، ترتیب مناسب این است:

### فاز 1: wallet MVP

appها:

- `wallet`
- `ledger`
- extend `addresses`

خروجی:

- wallet summary
- wallet accounts
- wallet transactions
- transaction detail

### فاز 2: commerce MVP

appها:

- `commerce_catalog`
- `cart`
- `checkout`
- `orders`
- `payments`

خروجی:

- خرید محصول فیزیکی
- خرید subscription مزرعه موجود
- پرداخت wallet/gateway

### فاز 3: onboarding advanced flow

appها:

- `farm_onboarding`
- `provisioning`
- `fulfillment`

خروجی:

- تحلیل طراحی مزرعه
- approval workflow
- installable devices

### فاز 4: channel integration hardening

appها:

- `merchant_integrations`
- `promotions`
- `billing`

خروجی:

- Woo sync کامل
- کوپن و کمپین
- فاکتور و اسناد مالی

---

## 22) پیشنهاد migration strategy

### مرحله 1

- app `wallet` و `ledger` ساخته شود.
- app `addresses` refactor شود.
- API wallet برای dashboard/page اضافه شود.

### مرحله 2

- app `commerce_catalog` ساخته شود.
- mapping با WooCommerce تعریف شود.
- data migration برای sync catalog طراحی شود.

### مرحله 3

- `cart`, `checkout`, `orders`, `payments` اضافه شوند.
- order/payment lifecycle پیاده شود.

### مرحله 4

- `farm_onboarding`, `provisioning`, `fulfillment` اضافه شوند.
- flow اولیه مزرعه و طراحی سنسور به checkout متصل شود.

---

## 23) تصمیم‌های مهمی که باید زود نهایی شوند

قبل از implementation بهتر است این تصمیم‌ها قطعی شوند:

1. آیا هر checkout فقط یک farm را پشتیبانی می‌کند یا multi-farm checkout لازم است؟
2. آیا wallet فقط برای پرداخت order است یا withdrawal واقعی هم دارد؟
3. آیا linked accountها حساب بانکی واقعی‌اند یا account نمایشی/داخلی؟
4. آیا Woo order shadow می‌سازد یا فقط catalog mirror است؟
5. آیا `farm_hub.Product` در آینده rename مفهومی می‌شود یا همان‌طور می‌ماند؟
6. آیا settlement و pending balance تعریف بانکی واقعی دارند یا صرفاً status داخلی هستند؟
7. آیا اپراتور review فقط برای onboarding اول است یا برای خریدهای خاص آینده هم لازم می‌شود؟

---

## 24) جمع‌بندی پیشنهاد نهایی appها

### appهای جدید اصلی

- `commerce_catalog`
- `cart`
- `checkout`
- `orders`
- `payments`
- `wallet`
- `ledger`
- `provisioning`
- `farm_onboarding`

### appهای تکمیلی پیشنهادی

- `pricing`
- `promotions`
- `fulfillment`
- `merchant_integrations`
- `billing`
- `customer_profiles`

### appهای موجود که باید تغییر کنند

- `farm_hub`
- `subscriptions`
- `access_control`
- `addresses`
- `device_hub`
- `dashboard`

---

## 25) پیشنهاد نهایی برای شروع پیاده‌سازی در همین repo

اگر بخواهم این repo را با کمترین اصطکاک توسعه بدهم، ترتیب پیشنهاد من این است:

1. اول `wallet`, `ledger` و refactor `addresses`
2. بعد `commerce_catalog`, `cart`, `checkout`
3. بعد `orders`, `payments`
4. بعد `farm_onboarding`, `provisioning`, `fulfillment`
5. در پایان `merchant_integrations`, `promotions`, `billing`

دلیل این ترتیب:

- UI فعلی wallet سریع‌تر unblock می‌شود.
- مدل‌های مالی و آدرس از ابتدا درست می‌شوند.
- بعد از آن checkout و order بر پایه درست سوار می‌شوند.
- onboarding پیچیده و async به فاز بعدی منتقل می‌شود.

---

## 26) ترتیب پیاده‌سازی پیشنهادی به‌صورت اجرایی

این بخش، ترتیب عملی implementation را به شکلی می‌دهد که:

- dependencyها رعایت شوند
- سریع‌ترین value برای frontend و admin panel تولید شود
- migration ریسک کمتری داشته باشد
- appها از ابتدا قابل تست و قابل توسعه بمانند

### فاز صفر: تثبیت مفاهیم دامنه و قراردادها

قبل از نوشتن مدل‌ها:

1. نهایی‌سازی enumها
   - `item_type`
   - `order_status`
   - `payment_status`
   - `wallet_transaction_type`
   - `address_type`
   - `onboarding_status`
2. نهایی‌سازی ownership ruleها
   - wallet در سطح user
   - order در سطح user + farm
   - checkout در یک farm context
3. نهایی‌سازی response contractهای frontend
   - wallet summary
   - wallet transactions
   - order detail
   - checkout session
4. نهایی‌سازی admin permission roleها

خروجی این فاز:

- مستند enumها
- مستند API contractهای MVP
- تصمیم قطعی درباره single-farm checkout

### فاز 1: refactor `addresses` و زیرساخت location

اولین پیاده‌سازی واقعی باید `addresses` باشد، چون تقریباً همه flowها به آن وابسته‌اند.

کارها:

1. refactor مدل `Address`
2. افزودن `uuid`, `label`, `address_type`, `recipient_name`, `recipient_phone`
3. افزودن `latitude`, `longitude`, `delivery_instructions`, `metadata`
4. افزودن relation اختیاری به `FarmHub`
5. ساخت endpointهای جدید `api/addresses/...`
6. ساخت endpointهای admin برای addresses
7. نگه‌داشتن endpoint قبلی به‌صورت deprecated

چرا اول؟

- checkout بدون address model درست ناقص می‌ماند.
- fulfillment و installation بدون farm location قابل طراحی نیست.
- admin panel برای order support به address snapshot نیاز دارد.

خروجی این فاز:

- app `addresses` قابل استفاده برای user و admin
- آماده شدن پایه برای checkout و fulfillment

### فاز 2: `wallet` + `ledger` + wallet admin APIs

این فاز بهترین نقطه برای unblock کردن UI فعلی wallet است.

کارها:

1. ساخت app `wallet`
2. ساخت app `ledger`
3. تعریف `Wallet`, `WalletTransaction`, `LedgerAccount`, `JournalEntry`, `JournalLine`
4. پیاده‌سازی posting service بین wallet و ledger
5. ساخت APIهای:
   - `GET /api/wallet/summary/`
   - `GET /api/wallet/accounts/`
   - `GET /api/wallet/transactions/`
   - `GET /api/wallet/transactions/{id}/`
6. ساخت APIهای admin:
   - `GET /api/admin/wallets/`
   - `POST /api/admin/wallets/{uuid}/adjust-balance/`
   - `POST /api/admin/wallets/{uuid}/manual-refund/`
7. اتصال dashboard wallet card به app جدید

چرا دوم؟

- نیاز UI شما را مستقیم پوشش می‌دهد.
- الگوی transaction/ledger برای payment و refundهای بعدی آماده می‌شود.

خروجی این فاز:

- wallet MVP کامل
- admin financial support MVP

### فاز 3: `commerce_catalog` + bridge اولیه WooCommerce

بعد از wallet، باید catalog داخلی ساخته شود تا از `farm_hub.Product` جدا شوید.

کارها:

1. ساخت app `commerce_catalog`
2. تعریف `SellableItem`, `SellableItemVariant`, `ExternalCatalogMapping`
3. تعریف item behavior flags
4. ساخت APIهای catalog برای frontend
5. ساخت APIهای admin catalog
6. تعریف sync contract با WooCommerce plugin

چرا قبل از cart؟

- cart باید روی sellable item واقعی کار کند، نه روی مدل crop فعلی.
- mapping با Woo از ابتدا باید روی entity درست بنشیند.

خروجی این فاز:

- catalog داخلی مستقل
- پایه‌ی سالم برای cart و checkout

### فاز 4: `cart`

وقتی catalog و address آماده شد، cart قابل پیاده‌سازی است.

کارها:

1. ساخت app `cart`
2. تعریف `Cart` و `CartItem`
3. پیاده‌سازی add/remove/update item
4. پشتیبانی از mixed cart
5. validate کردن requirementها در سطح item
6. attach کردن farm یا draft farm به cart item
7. ساخت APIهای cart
8. ساخت admin read-only API برای بررسی cartهای مشکل‌دار

چرا اینجا؟

- cart به catalog نیاز دارد.
- cart validation به address/farm requirement flags نیاز دارد.

خروجی این فاز:

- cart MVP
- mixed-item cart support

### فاز 5: `checkout`

این فاز orchestration اصلی را می‌سازد.

کارها:

1. ساخت app `checkout`
2. تعریف `CheckoutSession`
3. attach کردن address snapshotها
4. pricing snapshot اولیه
5. requirement engine
6. attach کردن farm یا onboarding session
7. confirm checkout و lock cart
8. ساخت APIهای user-facing checkout
9. ساخت APIهای admin برای force-expire / force-cancel / recalculate

dependencyها:

- catalog
- cart
- addresses
- wallet برای payment preparation

خروجی این فاز:

- multi-step checkout MVP
- پایه‌ی ورود به payment و order creation

### فاز 6: `orders` + `payments`

در این مرحله commerce هسته‌ای واقعی کامل می‌شود.

کارها:

1. ساخت app `orders`
2. ساخت app `payments`
3. تعریف `Order`, `OrderItem`, `PaymentIntent`, `PaymentAttempt`
4. ساخت order creation از checkout
5. ساخت gateway flow
6. ساخت wallet payment flow
7. ساخت hybrid payment flow در صورت نیاز
8. ساخت receipt endpoint
9. ساخت admin order APIs
10. ساخت admin payment APIs

چرا بعد از checkout؟

- order باید از checkout finalized ساخته شود.
- payment intent باید روی price freeze شده ساخته شود.

خروجی این فاز:

- ثبت سفارش
- پرداخت
- refund request پایه
- admin order/payment operations

### فاز 7: `fulfillment`

بعد از اینکه order ساخته می‌شود، fulfillment اهمیت پیدا می‌کند.

کارها:

1. ساخت app `fulfillment`
2. تعریف `Shipment` و `InstallationRequest`
3. ساخت shipment lifecycle
4. ساخت installation scheduling
5. ساخت admin fulfillment APIs
6. اتصال به address snapshotهای order

چرا این فاز جداست؟

- برای MVP اولیه پرداخت شاید هنوز fulfillment دستی باشد.
- جدا کردنش باعث می‌شود order/payment سریع‌تر بالا بیاید.

خروجی این فاز:

- shipment tracking پایه
- installable item operation flow

### فاز 8: `farm_onboarding`

این فاز پیچیده‌ترین بخش domain شما است و بهتر است بعد از commerce core بیاید.

کارها:

1. ساخت app `farm_onboarding`
2. تعریف `FarmOnboardingSession` و `FarmOnboardingRecommendation`
3. collect کردن farm setup data
4. ذخیره map/block/crop/irrigation data
5. اجرای async analysis
6. ساخت status polling
7. ساخت admin review APIs
8. attach کردن onboarding session به checkout

چرا دیرتر؟

- domain complexity بالا دارد.
- به cart/checkout/order نیازمند است.

خروجی این فاز:

- onboarding اولیه مزرعه
- analysis workflow
- operator review flow

### فاز 9: `provisioning`

بعد از onboarding و order/payment، provisioning automation را اضافه کنید.

کارها:

1. ساخت app `provisioning`
2. تعریف `ProvisioningTask`
3. taskهای:
   - `activate_subscription`
   - `rebuild_access_profile`
   - `create_farm_hub`
   - `attach_devices`
4. ساخت admin provisioning APIs
5. اتصال با `access_control`
6. اتصال با `device_hub`

خروجی این فاز:

- activation بعد از خرید
- sync operational resources

### فاز 10: `promotions`, `billing`, `merchant_integrations` hardening

این فاز برای production-readiness و کامل شدن کسب‌وکار است.

کارها:

1. app `promotions`
2. app `billing`
3. app `merchant_integrations`
4. Woo sync کامل
5. invoice/tax documents
6. campaign/coupon rules
7. admin reporting/metrics تکمیلی

خروجی این فاز:

- commerce production hardening
- marketing و accounting readiness

### ترتیب خلاصه‌شده appها

ترتیب نهایی پیشنهادی:

1. `addresses`
2. `wallet`
3. `ledger`
4. `commerce_catalog`
5. `cart`
6. `checkout`
7. `orders`
8. `payments`
9. `fulfillment`
10. `farm_onboarding`
11. `provisioning`
12. `promotions`
13. `billing`
14. `merchant_integrations`

### اگر بخواهید سریع‌ترین MVP را بسازید

MVP کوتاه‌تر:

1. `addresses`
2. `wallet`
3. `ledger`
4. `commerce_catalog`
5. `cart`
6. `checkout`
7. `orders`
8. `payments`

و در این مرحله:

- wallet UI کامل می‌شود
- خرید ساده کالا و subscription فعال می‌شود
- admin مالی و order support پایه آماده می‌شود

### اگر بخواهید admin panel را زودتر آماده کنید

پیشنهاد خاص برای admin-first:

1. `addresses` admin APIs
2. `wallet` admin APIs
3. `catalog` admin APIs
4. `orders` admin read APIs
5. `payments` admin reconciliation APIs
6. `farm_onboarding` review APIs

یعنی حتی قبل از کامل شدن همه flowهای user-facing، پنل عملیات و پشتیبانی می‌تواند آماده شود.

---

## 27) خروجی مورد انتظار این سند برای implementation

این سند باید مبنای کارهای بعدی زیر باشد:

- ساخت appها
- طراحی modelها
- تعریف serializerها
- طراحی endpointها
- تعیین state machineها
- برنامه‌ریزی migrationها
- شکستن کارها به milestoneهای توسعه

اگر بخواهید، قدم بعدی منطقی این است که بر اساس همین سند، من برای شما:

- structure اولیه appها را بسازم،
- modelهای MVP را تعریف کنم،
- و فایل phase-by-phase implementation plan هم جدا بنویسم.
