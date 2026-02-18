from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("auth.urls")),
    path("api/account/", include("account.urls")),
    path("api/sensor-hub/", include("sensor_hub.urls")),
]
