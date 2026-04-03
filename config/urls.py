from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/docs/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/auth/", include("auth.urls")),
    path("api/account/", include("account.urls")),
    path("api/farm-hub/", include("farm_hub.urls")),
    path("api/access-control/", include("access_control.urls")),
    path("api/sensor-catalog/", include("sensor_catalog.urls")),
    path("api/farm-dashboard-config/", include("dashboard.urls_config")),
    path("api/farm-dashboard/", include("dashboard.urls")),
    path("api/crop-zoning/", include("crop_zoning.urls")),
    path("api/plant-simulator/", include("plant_simulator.urls")),
    path("api/pest-detection/", include("pest_detection.urls")),
    path("api/irrigation-recommendation/", include("irrigation_recommendation.urls")),
    path("api/fertilization-recommendation/", include("fertilization_recommendation.urls")),
    path("api/farm-ai-assistant/", include("farm_ai_assistant.urls")),
    path("api/notifications/", include("notifications.urls")),
]
