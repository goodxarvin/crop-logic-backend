from django.urls import path

from .views import (
    AreaView,
    ProductsView,
    ZoneDetailsView,
    ZonesCultivationRiskView,
    ZonesInitialView,
    ZonesSoilQualityView,
    ZonesWaterNeedView,
)

urlpatterns = [
    path("area/", AreaView.as_view(), name="crop-zoning-area"),
    path("products/", ProductsView.as_view(), name="crop-zoning-products"),
    path("zones/initial/", ZonesInitialView.as_view(), name="crop-zoning-zones-initial"),
    path(
        "zones/water-need/",
        ZonesWaterNeedView.as_view(),
        name="crop-zoning-zones-water-need",
    ),
    path(
        "zones/soil-quality/",
        ZonesSoilQualityView.as_view(),
        name="crop-zoning-zones-soil-quality",
    ),
    path(
        "zones/cultivation-risk/",
        ZonesCultivationRiskView.as_view(),
        name="crop-zoning-zones-cultivation-risk",
    ),
    path(
        "zones/<str:zone_id>/details/",
        ZoneDetailsView.as_view(),
        name="crop-zoning-zone-details",
    ),
]
