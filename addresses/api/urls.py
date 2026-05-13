from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

app_name = "address-api-urls"

router = DefaultRouter()
router.register("", views.AddressViewSet, basename="address-viewset")

urlpatterns = [
    path("province/", views.ProvinceListAPIView.as_view(), name="get-provinces"),
    path("province/<int:province_pk>/cities/", views.CityListAPIView.as_view(), name="get-cities")
]

urlpatterns += router.urls