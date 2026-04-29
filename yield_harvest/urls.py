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
    path("summary/", YieldHarvestSummaryView.as_view(), name="yield-harvest-summary"),
    path("current-farm-chart/", CurrentFarmChartView.as_view(), name="yield-harvest-current-farm-chart"),
    path("growth/", GrowthSimulationView.as_view(), name="yield-harvest-growth"),
    path("growth/<str:task_id>/status/", GrowthSimulationStatusView.as_view(), name="yield-harvest-growth-status"),
    path("harvest-prediction/", HarvestPredictionView.as_view(), name="yield-harvest-harvest-prediction"),
    path("yield-prediction/", YieldPredictionView.as_view(), name="yield-harvest-yield-prediction"),
    path("yield-harvest-summary/", YieldHarvestSummaryView.as_view(), name="yield-harvest-crop-simulation-summary"),
]
