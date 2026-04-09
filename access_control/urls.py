from django.urls import path

from .views import FarmFeatureAuthorizationView

urlpatterns = [
    path("farms/<uuid:farm_uuid>/authorize/", FarmFeatureAuthorizationView.as_view(), name="farm-feature-authorization"),
]
