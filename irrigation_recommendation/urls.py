from django.urls import path

from .views import ConfigView, RecommendTaskStatusView, RecommendView

urlpatterns = [
    path("config/", ConfigView.as_view(), name="irrigation-recommendation-config"),
    path("recommend/", RecommendView.as_view(), name="irrigation-recommendation-recommend"),
    path(
        "recommend/status/<str:task_id>/",
        RecommendTaskStatusView.as_view(),
        name="irrigation-recommendation-task-status",
    ),
]
