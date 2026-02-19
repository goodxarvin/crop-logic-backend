from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("auth.urls")),
    path("api/account/", include("account.urls")),
    path("api/sensor-hub/", include("sensor_hub.urls")),
    path("api/farm-dashboard-config/", include("dashboard.urls_config")),
    path("api/farm-dashboard/", include("dashboard.urls")),
]
