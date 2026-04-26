from django.urls import path

from .views import (
    AvgSoilMoistureView,
    SoilAnomalyDetectionView,
    SoilMoistureHeatmapView,
    SoilSummaryView,
)

urlpatterns = [
    path("avg-moisture/", AvgSoilMoistureView.as_view(), name="soil-avg-moisture"),
    path("anomalies/", SoilAnomalyDetectionView.as_view(), name="soil-anomalies"),
    path("moisture-heatmap/", SoilMoistureHeatmapView.as_view(), name="soil-moisture-heatmap"),
    path("summary/", SoilSummaryView.as_view(), name="soil-summary"),
]
