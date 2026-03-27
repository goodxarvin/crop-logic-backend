from django.urls import path

from .views import ConfigView, RecommendView

urlpatterns = [
    path("config/", ConfigView.as_view(), name="fertilization-recommendation-config"),
    path("recommend/", RecommendView.as_view(), name="fertilization-recommendation-recommend"),
]
