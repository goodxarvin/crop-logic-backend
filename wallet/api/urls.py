from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# from django.urls import path

router = DefaultRouter()
router.register("wallets", views.WalletListView, basename="wallets")
router.register("transactions", views.TransactionListView, basename="transactions")

urlpatterns = [
    path("wallets/topup/", views.WalletTopupAPIView.as_view(), name="wallet-topup"),
    path(
        "wallets/topup/callback/",
        views.WalletTopupCallbackAPIView.as_view(),
        name="wallet-callback",
    ),
]

urlpatterns += router.urls
