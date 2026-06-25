from django.urls import path, include

app_name = "addresses"

urlpatterns = [path("", include("address.api.urls"), name="address-api")]
