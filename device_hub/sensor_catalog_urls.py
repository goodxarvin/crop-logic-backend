from django.urls import path

from .views import DeviceCatalogListView

urlpatterns = [
    path("", DeviceCatalogListView.as_view(), name="sensor-catalog-list"),
]
