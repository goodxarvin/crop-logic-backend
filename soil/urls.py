from django.urls import path

from .views import (
    AvgSoilMoistureView,
    SensorComparisonChartView,
    SensorRadarChartView,
    SoilAnomalyDetectionView,
    SoilMoistureHeatmapView,
    SoilSummaryView,
)

urlpatterns = [
    path("avg-moisture/", AvgSoilMoistureView.as_view(), name="soil-avg-moisture"),
    path("sensor-radar-chart/", SensorRadarChartView.as_view(), name="soil-sensor-radar-chart"),
    path("sensor-comparison-chart/", SensorComparisonChartView.as_view(), name="soil-sensor-comparison-chart"),
    path("anomalies/", SoilAnomalyDetectionView.as_view(), name="soil-anomalies"),
    path("moisture-heatmap/", SoilMoistureHeatmapView.as_view(), name="soil-moisture-heatmap"),
    path("summary/", SoilSummaryView.as_view(), name="soil-summary"),
]
