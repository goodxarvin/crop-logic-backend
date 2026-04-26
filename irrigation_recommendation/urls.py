from django.urls import path

from .views import ConfigView, IrrigationMethodListView, RecommendView, WaterStressView

urlpatterns = [
    path("", IrrigationMethodListView.as_view(), name="irrigation-method-list"),
    path("config/", ConfigView.as_view(), name="irrigation-recommendation-config"),
    path("recommend/", RecommendView.as_view(), name="irrigation-recommendation-recommend"),
    path("water-stress/", WaterStressView.as_view(), name="irrigation-water-stress"),
]
