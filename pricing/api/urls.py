from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter
from . import views

router = DefaultRouter()
router.register("base-prices", views.BasePriceViewSet, basename="base-prices")
router.register("price-tiers", views.PriceTierViewSet, basename="price-tiers")
router.register("price-history", views.PriceHistoryViewSet, basename="price-history")
router.register("currencies", views.CurrencyViewSet, basename="currencies")
router.register("discounts", views.DiscountPriceViewSet, basename="discounts")

currency_router = NestedDefaultRouter(router, "currencies", lookup="currency")
currency_router.register(
    "base-prices", views.BasePriceViewSet, basename="currency-base-prices"
)
currency_router.register(
    "price-tiers", views.PriceTierViewSet, basename="currency-price-tiers"
)

discount_router = NestedDefaultRouter(router, "discounts", lookup="discount")
discount_router.register(
    "sku-relations", views.DiscountSKURelationViewSet, basename="discount-sku-relations"
)
discount_router.register(
    "sellable-item-relations",
    views.DiscountSellableItemRelationViewSet,
    basename="discount-sellable-item-relations",
)

urlpatterns = router.urls
urlpatterns += currency_router.urls
urlpatterns += discount_router.urls
