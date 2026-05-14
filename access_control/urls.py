from django.urls import path

from .views import FarmFeatureAuthorizationView, PanelRoutingView

urlpatterns = [
    path("farms/<uuid:farm_uuid>/authorize/", FarmFeatureAuthorizationView.as_view(), name="farm-feature-authorization"),
    path("panel-routing/", PanelRoutingView.as_view(), name="panel-routing"),
]
