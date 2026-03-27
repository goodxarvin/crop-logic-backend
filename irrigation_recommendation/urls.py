from django.urls import path

from .views import ConfigView, RecommendView

urlpatterns = [
    path("config/", ConfigView.as_view(), name="irrigation-recommendation-config"),
    path("recommend/", RecommendView.as_view(), name="irrigation-recommendation-recommend"),
]
