from django.urls import path

from .views import CropHealthSummaryView

urlpatterns = [
    path("summary/", CropHealthSummaryView.as_view(), name="crop-health-summary"),
]
