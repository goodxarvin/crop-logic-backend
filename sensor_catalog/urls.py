from django.urls import path

from .views import SensorCatalogListView

urlpatterns = [
    path("", SensorCatalogListView.as_view(), name="sensor-catalog-list"),
]
