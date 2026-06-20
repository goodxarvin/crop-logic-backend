from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# from django.urls import path

router = DefaultRouter()
router.register("wallets", views.WalletListViewset, basename="wallets")
router.register("transactions", views.TransactionListViewset, basename="transactions")
router.register(
    "my-transactions", views.UserTransactionViewset, basename="my-transactions"
)

urlpatterns = [
    path("wallets/topup/", views.WalletTopupAPIView.as_view(), name="wallet-topup"),
    path(
        "wallets/topup/callback/",
        views.WalletTopupCallbackAPIView.as_view(),
        name="wallet-callback",
    ),
    path("my-wallet/", views.UserWalletRetrieveAPIView.as_view(), name="my-wallet"),
]

urlpatterns += router.urls
