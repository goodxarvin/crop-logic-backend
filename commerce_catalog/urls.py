from django.urls import path, include

app_name = "commerce-catalog"

urlpatterns = [path("", include("commerce_catalog.api.urls"))]
