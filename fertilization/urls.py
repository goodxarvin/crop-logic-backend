from django.urls import path

from .views import (
    ConfigView,
    FertilizationPlanDetailView,
    FertilizationPlanListView,
    FertilizationPlanStatusView,
    PlanFromTextView,
    RecommendationDetailView,
    RecommendationListView,
    RecommendView,
)

urlpatterns = [
    path("config/", ConfigView.as_view(), name="fertilization-recommendation-config"),
    path("plans/", FertilizationPlanListView.as_view(), name="fertilization-plan-list"),
    path("plans/<uuid:plan_uuid>/", FertilizationPlanDetailView.as_view(), name="fertilization-plan-detail"),
    path("plans/<uuid:plan_uuid>/status/", FertilizationPlanStatusView.as_view(), name="fertilization-plan-status"),
    path("recommendations/<uuid:recommendation_uuid>/", RecommendationDetailView.as_view(), name="fertilization-recommendation-detail"),
    path("recommendations/", RecommendationListView.as_view(), name="fertilization-recommendation-list"),
    path("recommend/", RecommendView.as_view(), name="fertilization-recommendation-recommend"),
    path("plan-from-text/", PlanFromTextView.as_view(), name="fertilization-plan-from-text"),
]
