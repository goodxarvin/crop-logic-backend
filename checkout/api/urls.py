from rest_framework.routers import DefaultRouter
from .views import CheckoutViewset

router = DefaultRouter()
router.register("checkouts", CheckoutViewset, basename="checkouts")


urlpatterns = router.urls
