from rest_framework.routers import DefaultRouter
from . import views

# from django.urls import path

router = DefaultRouter()
router.register("wallets", views.WalletListView, basename="wallets")
router.register("transactions", views.TransactionListView, basename="transactions")

urlpatterns = router.urls
