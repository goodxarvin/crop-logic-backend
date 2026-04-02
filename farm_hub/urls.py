from django.urls import path

from .views import FarmActiveView, FarmDeactiveView, FarmDetailView, FarmListCreateView

urlpatterns = [
    path("active/", FarmActiveView.as_view(), name="farm-hub-active"),
    path("deactive/", FarmDeactiveView.as_view(), name="farm-hub-deactive"),
    path("<uuid:farm_uuid>/", FarmDetailView.as_view(), name="farm-hub-detail"),
    path("", FarmListCreateView.as_view(), name="farm-hub-list"),
]
