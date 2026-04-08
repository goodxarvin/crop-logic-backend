from django.urls import path

from .views import (
    AreaView,
    CultivationRiskView,
    ProductsView,
    SoilQualityView,
    WaterNeedView,
    ZoneDetailsView,
    ZonesCultivationRiskView,
    ZonesInitialView,
    ZonesSoilQualityView,
    ZonesWaterNeedView,
)

urlpatterns = [
    path("area/", AreaView.as_view(), name="crop-zoning-area"),
    path("water-need/", WaterNeedView.as_view(), name="crop-zoning-water-need"),
    path("soil-quality/", SoilQualityView.as_view(), name="crop-zoning-soil-quality"),
    path("cultivation-risk/", CultivationRiskView.as_view(), name="crop-zoning-cultivation-risk"),
    path("products/", ProductsView.as_view(), name="crop-zoning-products"),
    # path("zones/initial/", ZonesInitialView.as_view(), name="crop-zoning-zones-initial"),
    # path(
    #     "zones/water-need/",
    #     ZonesWaterNeedView.as_view(),
    #     name="crop-zoning-zones-water-need",
    # ),
    # path(
    #     "zones/soil-quality/",
    #     ZonesSoilQualityView.as_view(),
    #     name="crop-zoning-zones-soil-quality",
    # ),
    # path(
    #     "zones/cultivation-risk/",
    #     ZonesCultivationRiskView.as_view(),
    #     name="crop-zoning-zones-cultivation-risk",
    # ),
    path(
        "zones/<str:zone_id>/details/",
        ZoneDetailsView.as_view(),
        name="crop-zoning-zone-details",
    ),
]
