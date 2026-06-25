from django.urls import path, include

urlpatterns = [
    path("", include("order.api.urls")),
]
