from django.urls import path

from .views import AnalyzeView, RiskSummaryView, RiskView

urlpatterns = [
    path("detect/", AnalyzeView.as_view(), name="pest-disease-detect"),
    path("risk/", RiskView.as_view(), name="pest-disease-risk"),
    path("risk-summary/", RiskSummaryView.as_view(), name="pest-disease-risk-summary"),
]
