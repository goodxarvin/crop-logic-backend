from rest_framework import routers
from .views import OrderViewset

app_name = "api-urls"

router = routers.DefaultRouter()
router.register("orders", OrderViewset, basename="orders")


urlpatterns = router.urls
