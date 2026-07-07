from django.urls import path, include

app_name = "address"

urlpatterns = [path("", include("address.api.urls"))]
