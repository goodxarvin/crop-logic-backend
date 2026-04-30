from django.urls import path

from .views import (
    ConfigView,
    IrrigationMethodListView,
    PlanFromTextView,
    RecommendationDetailView,
    RecommendationListView,
    RecommendView,
    WaterStressView,
)

urlpatterns = [
    path("", IrrigationMethodListView.as_view(), name="irrigation-method-list"),
    path("config/", ConfigView.as_view(), name="irrigation-recommendation-config"),
    path("recommendations/<uuid:recommendation_uuid>/", RecommendationDetailView.as_view(), name="irrigation-recommendation-detail"),
    path("recommendations/", RecommendationListView.as_view(), name="irrigation-recommendation-list"),
    path("recommend/", RecommendView.as_view(), name="irrigation-recommendation-recommend"),
    path("plan-from-text/", PlanFromTextView.as_view(), name="irrigation-plan-from-text"),
    path("water-stress/", WaterStressView.as_view(), name="irrigation-water-stress"),
]
