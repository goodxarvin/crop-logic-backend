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
    path("api/crop-health/", include("crop_health.urls")),
    path("api/soil/", include("soil.urls")),

    path("api/crop-zoning/", include("crop_zoning.urls")),
    # path("api/yield-harvest/", include("yield_harvest.urls")),
    path("api/yield-harvest/", include("yield_harvest.crop_simulation_urls")),

    path("api/pest-detection/", include("pest_detection.urls")),
    path("api/pest-disease/", include("pest_detection.pest_disease_urls")),
    path("api/sensor-7-in-1/", include("sensor_7_in_1.urls")),
    path("api/sensors/", include("sensor_7_in_1.comparison_urls")),
    path("api/irrigation/", include("irrigation_recommendation.urls")),

    path("api/weather/", include("water.weather_urls")),
    path("api/water/", include("water.urls")),
    path("api/economy/", include("economic_overview.urls")),

    path("api/fertilization/", include("fertilization_recommendation.urls")),
    path("api/farm-ai-assistant/", include("farm_ai_assistant.urls")),
    path("api/notifications/", include("notifications.urls")),
    path("api/farm-alerts/", include("farm_alerts.urls")),
    path("api/plants/", include("plants.urls")),

    path("api/sensor-external-api/", include("sensor_external_api.urls")),
]
