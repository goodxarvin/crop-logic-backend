from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter
from . import views
from pricing.api.views import (
    PriceTierViewSet,
    PriceHistoryViewSet,
    DiscountSellableItemRelationViewSet,
    DiscountSKURelationViewSet,
)

app_name = "api-urls"

router = DefaultRouter()
router.register("sellable-items", views.SellableItemViewSet, basename="sellable-items")
router.register("tax-classes", views.TaxClassViewSet, basename="tax-classes")
router.register(
    "product-add-ons", views.ProductAddOnViewSet, basename="product-add-ons"
)
router.register("bundles", views.ProductBundleViewSet, basename="bundles")

add_on_router = NestedDefaultRouter(router, "product-add-ons", lookup="product_add_on")
add_on_router.register(
    "add-on-assignments", views.AddOnAssignmentViewSet, basename="add-on-assignments"
)

sellable_router = NestedDefaultRouter(router, "sellable-items", lookup="sellable_item")
sellable_router.register("variants", views.ProductVariantViewSet, basename="variants")
sellable_router.register("skus", views.SKUViewset, basename="sku")
sellable_router.register(
    "add-on-assignments", views.AddOnAssignmentViewSet, basename="add-on-assignments"
)
sellable_router.register(
    "dicsount-sellable-item-relations",
    DiscountSellableItemRelationViewSet,
    basename="discount-sellable-item-relations",
)

variants_router = NestedDefaultRouter(sellable_router, "variants", lookup="variant")
variants_router.register(
    "attributes", views.ProductAttributeValueViewSet, basename="attributes"
)

sku_router = NestedDefaultRouter(sellable_router, "skus", lookup="sku")
sku_router.register(
    "bundle-items", views.ProductBundleItemViewSet, basename="bundle-items"
)
sku_router.register("price-tiers", PriceTierViewSet, basename="price-tiers")
sku_router.register("price-history", PriceHistoryViewSet, basename="price-history")
sku_router.register(
    "discount-sku-relations",
    DiscountSKURelationViewSet,
    basename="discount-sku-relations",
)

bundle_router = NestedDefaultRouter(router, "bundles", lookup="bundle")
bundle_router.register(
    "bundle-items", views.ProductBundleItemViewSet, basename="bundle-items"
)

# urlpatterns = [
#     path("sellable-items/", views.SellableItemListAPIView.as_view(), name="sellable-items-list")
# ]

urlpatterns = router.urls
urlpatterns += add_on_router.urls
urlpatterns += sellable_router.urls
urlpatterns += variants_router.urls
urlpatterns += sku_router.urls
urlpatterns += bundle_router.urls
