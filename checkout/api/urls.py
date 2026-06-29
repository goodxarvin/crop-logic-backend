from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

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
