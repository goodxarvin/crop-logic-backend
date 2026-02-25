from django.urls import path

from .views import InitialRegionView, OptimizeZoningView

urlpatterns = [
    path("optimize/", OptimizeZoningView.as_view(), name="crop-zoning-optimize"),
    path("initial-region/", InitialRegionView.as_view(), name="crop-zoning-initial-region"),
]
