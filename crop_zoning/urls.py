from django.urls import path

from .views import (
    ClusterBlockLiveView,
    ClusterRecommendationsView,
    KOptionsActivateView,
    KOptionsView,
    LocationDataNdviHealthView,
    LocationDataRemoteSensingView,
    LocationDataView,
    RunStatusView,
)

urlpatterns = [
    path("", LocationDataView.as_view(), name="location-data"),
    path("ndvi-health/", LocationDataNdviHealthView.as_view(), name="location-data-ndvi-health"),
    path("remote-sensing/", LocationDataRemoteSensingView.as_view(), name="location-data-remote-sensing"),
    path(
        "remote-sensing/cluster-blocks/<uuid:cluster_uuid>/live/",
        ClusterBlockLiveView.as_view(),
        name="location-data-cluster-block-live",
    ),
    path(
        "remote-sensing/cluster-recommendations/",
        ClusterRecommendationsView.as_view(),
        name="location-data-cluster-recommendations",
    ),
    path(
        "remote-sensing/results/<int:result_id>/k-options/",
        KOptionsView.as_view(),
        name="location-data-k-options",
    ),
    path(
        "remote-sensing/results/<int:result_id>/k-options/activate/",
        KOptionsActivateView.as_view(),
        name="location-data-k-options-activate",
    ),
    path(
        "remote-sensing/runs/<int:run_id>/status/",
        RunStatusView.as_view(),
        name="location-data-run-status",
    ),
]
