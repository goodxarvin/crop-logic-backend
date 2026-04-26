from django.urls import path

from .views import AlertTimelineView, AlertTrackerView

urlpatterns = [
    path("tracker/", AlertTrackerView.as_view(), name="farm-alerts-tracker"),
    path("timeline/", AlertTimelineView.as_view(), name="farm-alerts-timeline"),
]
