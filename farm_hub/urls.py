from django.urls import path

from .views import (
    FarmActiveView,
    FarmDeactiveView,
    FarmDetailView,
    FarmListCreateView,
    FarmTypeListView,
    FarmTypeProductsView,
)

urlpatterns = [
    path("active/", FarmActiveView.as_view(), name="farm-hub-active"),
    path("deactive/", FarmDeactiveView.as_view(), name="farm-hub-deactive"),
    path("farm-types/", FarmTypeListView.as_view(), name="farm-type-list"),
    path("farm-types/<uuid:farm_type_uuid>/products/", FarmTypeProductsView.as_view(), name="farm-type-products"),
    path("<uuid:farm_uuid>/", FarmDetailView.as_view(), name="farm-hub-detail"),
    path("", FarmListCreateView.as_view(), name="farm-hub-list"),
]
