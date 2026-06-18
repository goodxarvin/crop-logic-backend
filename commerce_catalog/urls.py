from django.urls import path, include

urlpatterns = [
    path("", include("commerce_catalog.api.urls"))
]