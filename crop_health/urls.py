from django.urls import path

from .views import CropHealthSummaryView, NdviHealthView

urlpatterns = [
    path("ndvi-health/", NdviHealthView.as_view(), name="crop-health-ndvi-health"),
    path("summary/", CropHealthSummaryView.as_view(), name="crop-health-summary"),
]
