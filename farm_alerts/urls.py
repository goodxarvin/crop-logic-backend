from django.urls import path

from .views import (
    AlertTrackerView,
    AlertTimelineView,
    AnomalyDetectionView,
    RecommendationsListView,
    CreateAlertView,
)

urlpatterns = [
    path("tracker/", AlertTrackerView.as_view(), name="farm-alerts-tracker"),
    path("timeline/", AlertTimelineView.as_view(), name="farm-alerts-timeline"),
    path("anomalies/", AnomalyDetectionView.as_view(), name="farm-alerts-anomalies"),
    path("recommendations/", RecommendationsListView.as_view(), name="farm-alerts-recommendations"),
    path("create/", CreateAlertView.as_view(), name="farm-alerts-create"),
]
