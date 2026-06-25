from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(
    "ledger-accounts",
    views.LedgerAccountViewSet,
    basename="ledger-accounts",
)
router.register(
    "ledger-transactions",
    views.LedgerTransactionViewSet,
    basename="ledger-transactions",
)
router.register(
    "ledger-line",
    views.LedgerLineViewSet,
    basename="ledger-line",
)

urlpatterns = router.urls
