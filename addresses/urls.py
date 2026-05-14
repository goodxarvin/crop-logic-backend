from django.urls import path, include

app_name = "addresses"

urlpatterns = [
    path("", include("addresses.api.urls"), name="address-api")
]