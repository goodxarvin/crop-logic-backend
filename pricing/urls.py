from django.urls import path, include

urlpatterns = [
    path("", include("pricing.api.urls")),
]
