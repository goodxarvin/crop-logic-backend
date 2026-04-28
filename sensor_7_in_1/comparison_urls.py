from django.urls import path

from .views import SensorComparisonChartView, SensorRadarChartView, SensorValuesListView


urlpatterns = [
    path("comparison-chart/", SensorComparisonChartView.as_view(), name="sensor-comparison-chart"),
    path("radar-chart/", SensorRadarChartView.as_view(), name="sensor-radar-chart"),
    path("values-list/", SensorValuesListView.as_view(), name="sensor-values-list"),
]
