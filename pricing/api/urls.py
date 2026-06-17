from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter
from . import views

router = DefaultRouter()
router.register("base-prices", views.BasePriceViewSet, basename="base-prices")
router.register("price-tiers", views.PriceTierViewSet, basename="price-tiers")
router.register("price-history", views.PriceHistoryViewSet, basename="price-history")


urlpatterns = router.urls
