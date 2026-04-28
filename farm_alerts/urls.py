from django.urls import path

from .views import AlertTrackerView

urlpatterns = [
    path("tracker/", AlertTrackerView.as_view(), name="farm-alerts-tracker"),
]
