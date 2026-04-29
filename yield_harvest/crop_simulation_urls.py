from django.urls import path

from .views import (
    CurrentFarmChartView,
    GrowthSimulationStatusView,
    GrowthSimulationView,
    HarvestPredictionView,
    YieldHarvestSummaryView,
    YieldPredictionView,
)

urlpatterns = [
    path("current-farm-chart/", CurrentFarmChartView.as_view(), name="crop-simulation-current-farm-chart"),
    path("growth/", GrowthSimulationView.as_view(), name="crop-simulation-growth"),
    path("growth/<str:task_id>/status/", GrowthSimulationStatusView.as_view(), name="crop-simulation-growth-status"),
    path("harvest-prediction/", HarvestPredictionView.as_view(), name="crop-simulation-harvest-prediction"),
    path("yield-harvest-summary/", YieldHarvestSummaryView.as_view(), name="crop-simulation-yield-harvest-summary"),
    path("yield-prediction/", YieldPredictionView.as_view(), name="crop-simulation-yield-prediction"),
]
