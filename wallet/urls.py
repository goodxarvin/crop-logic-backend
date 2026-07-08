from django.urls import path, include

app_name = "wallet"

urlpatterns = [
    path("", include("wallet.api.urls")),
]
