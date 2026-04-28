from django.urls import path

from .views import PlantDetailView, PlantListView, PlantNameListView, SelectedPlantListView

urlpatterns = [
    path("names/", PlantNameListView.as_view(), name="plant-name-list"),
    path("selected/", SelectedPlantListView.as_view(), name="selected-plant-list"),
    path("<int:plant_id>/", PlantDetailView.as_view(), name="plant-detail"),
    path("", PlantListView.as_view(), name="plant-list"),
]
