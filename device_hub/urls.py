from django.urls import path

from .views import DeviceCatalogListView, DeviceCodeListView, DeviceCommandView, DeviceComparisonChartView, DeviceDetailView, DeviceLatestPayloadView, DeviceLogListView, DeviceRadarChartView, DeviceSummaryView, DeviceValuesListView, Sensor7In1SummaryView, SensorExternalAPIView, SensorExternalRequestLogListAPIView

urlpatterns = [
    path("catalog/", DeviceCatalogListView.as_view(), name="device-catalog-list"),
    path("devices/<uuid:physical_device_uuid>/device-codes/", DeviceCodeListView.as_view(), name="device-code-list"),
    path("devices/<uuid:physical_device_uuid>/", DeviceDetailView.as_view(), name="device-detail"),
    path("devices/<uuid:physical_device_uuid>/latest/", DeviceLatestPayloadView.as_view(), name="device-latest-payload"),
    path("devices/<uuid:physical_device_uuid>/summary/", DeviceSummaryView.as_view(), name="device-summary"),
    path("devices/<uuid:physical_device_uuid>/values-list/", DeviceValuesListView.as_view(), name="device-values-list"),
    path("devices/<uuid:physical_device_uuid>/comparison-chart/", DeviceComparisonChartView.as_view(), name="device-comparison-chart"),
    path("devices/<uuid:physical_device_uuid>/radar-chart/", DeviceRadarChartView.as_view(), name="device-radar-chart"),
    path("devices/<uuid:physical_device_uuid>/logs/", DeviceLogListView.as_view(), name="device-log-list"),
    path("devices/<uuid:physical_device_uuid>/commands/", DeviceCommandView.as_view(), name="device-command"),
    path("summary/", Sensor7In1SummaryView.as_view(), name="sensor-7-in-1-summary"),
    path("", DeviceCatalogListView.as_view(), name="sensor-catalog-list"),
    path("external/", SensorExternalAPIView.as_view(), name="sensor-external-api"),
    path("external/logs/", SensorExternalRequestLogListAPIView.as_view(), name="sensor-external-api-log-list"),
]
