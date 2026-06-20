from django.urls import path, include

urlpatterns = [
    path("", include("wallet.api.urls")),
]
