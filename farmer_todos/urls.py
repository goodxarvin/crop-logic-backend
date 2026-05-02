from django.urls import path

from .views import (
    FarmerTodoDetailView,
    FarmerTodoListCreateView,
    FarmerTodoSummaryView,
    FarmerTodoTagsView,
    FarmerTodoZonesView,
)

urlpatterns = [
    path("zones/", FarmerTodoZonesView.as_view(), name="farmer-todo-zones"),
    path("tags/", FarmerTodoTagsView.as_view(), name="farmer-todo-tags"),
    path("summary/", FarmerTodoSummaryView.as_view(), name="farmer-todo-summary"),
    path("<uuid:task_id>/", FarmerTodoDetailView.as_view(), name="farmer-todo-detail"),
    path("", FarmerTodoListCreateView.as_view(), name="farmer-todo-list-create"),
]
