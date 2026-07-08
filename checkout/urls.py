from django.urls import path, include

app_name = "customer_notes"

urlpatterns = [
    path("", include("checkout.api.urls")),
]
