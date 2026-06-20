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
router.register(
    "pending-withdrawals", views.AdminPendingViewset, basename="pending-withdrawal"
)

urlpatterns = [
    path(
        "topup/",
        views.WalletTopupAPIView.as_view(),
        name="wallet-topup",
    ),
    path(
        "topup/callback/",
        views.WalletTopupCallbackAPIView.as_view(),
        name="wallet-callback",
    ),
    path(
        "my-wallet/",
        views.UserWalletRetrieveAPIView.as_view(),
        name="my-wallet",
    ),
    path(
        "withdrawal-request/",
        views.UserWithdrawalRequestAPIView.as_view(),
        name="user-withdrawal-request",
    ),
    path(
        "process-withdrawal/<uuid:uuid>/<str:action_type>/",
        views.AdminWithdrawalProcessAPIView.as_view(),
        name="process-withdrawal",
    ),
]

urlpatterns += router.urls
