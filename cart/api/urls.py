from rest_framework import routers
from .views import CartItemViewSet, CartViewset

router = routers.DefaultRouter()
router.register("cart-items", CartItemViewSet, basename="cart-items")
router.register("user-carts", CartViewset, basename="user-carts")

urlpatterns = router.urls
