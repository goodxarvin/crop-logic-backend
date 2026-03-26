from django.urls import path

from .views import ConfigView, RecommendTaskStatusView, RecommendView

urlpatterns = [
    path("config/", ConfigView.as_view(), name="fertilization-recommendation-config"),
    path("recommend/", RecommendView.as_view(), name="fertilization-recommendation-recommend"),
    # path("recommend/task/", RecommendTaskCreateView.as_view(), name="fertilization-recommendation-task-create"),
    path("recommend/<str:task_id>/status/", RecommendTaskStatusView.as_view(), name="fertilization-recommendation-task-status"),
]
