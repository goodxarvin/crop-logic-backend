from django.urls import path

from .views import Sensor7In1SummaryView, SensorCatalogListView, SensorExternalAPIView, SensorExternalRequestLogListAPIView

urlpatterns = [
    path("summary/", Sensor7In1SummaryView.as_view(), name="sensor-7-in-1-summary"),
    path("", SensorCatalogListView.as_view(), name="sensor-catalog-list"),
    path("external/", SensorExternalAPIView.as_view(), name="sensor-external-api"),
    path("external/logs/", SensorExternalRequestLogListAPIView.as_view(), name="sensor-external-api-log-list"),
]

