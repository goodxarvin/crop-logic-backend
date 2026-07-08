from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

app_name = "api-urls"


router = DefaultRouter()
router.register("checkouts", views.CheckoutViewset, basename="checkouts")

urlpatterns = [
    path(
        "initiate/",
        views.InitiateCheckoutAPIView.as_view(),
        name="checkout-initiate",
    ),
    path(
        "callback/",
        views.VerifyCheckoutAPIView.as_view(),
        name="checkout-callback",
    ),
]

urlpatterns += router.urls
