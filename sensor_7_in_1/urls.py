from django.urls import path

from .views import Sensor7In1ComparisonChartView, Sensor7In1RadarChartView, Sensor7In1SummaryView


urlpatterns = [
    path("summary/", Sensor7In1SummaryView.as_view(), name="sensor-7-in-1-summary"),
    path("sensor-radar-chart/", Sensor7In1RadarChartView.as_view(), name="sensor-7-in-1-radar-chart"),
    path(
        "sensor-comparison-chart/",
        Sensor7In1ComparisonChartView.as_view(),
        name="sensor-7-in-1-comparison-chart",
    ),
]
