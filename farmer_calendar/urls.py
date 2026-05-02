from django.urls import path

from .views import EventDetailView, EventListCreateView, EventTagListView

urlpatterns = [
    path("tags/", EventTagListView.as_view(), name="farmer-calendar-tag-list"),
    path("<uuid:event_id>/", EventDetailView.as_view(), name="farmer-calendar-detail"),
    path("", EventListCreateView.as_view(), name="farmer-calendar-list-create"),
]
