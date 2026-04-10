from django.urls import path

from .views import AnalyzeView, RiskSummaryView

urlpatterns = [
    path("analyze/", AnalyzeView.as_view(), name="pest-detection-analyze"),
    path("risk-summary/", RiskSummaryView.as_view(), name="pest-detection-risk-summary"),
]
