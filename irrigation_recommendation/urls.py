from django.urls import path

from .views import ConfigView, RecommendTaskCreateView, RecommendTaskStatusView, RecommendView

urlpatterns = [
    path("config/", ConfigView.as_view(), name="irrigation-recommendation-config"),
    path("recommend/", RecommendView.as_view(), name="irrigation-recommendation-recommend"),
    path("recommend/task/", RecommendTaskCreateView.as_view(), name="irrigation-recommendation-task-create"),
    path("recommend/<str:task_id>/status/", RecommendTaskStatusView.as_view(), name="irrigation-recommendation-task-status"),
]
