from django.urls import path

from .views import NotificationPublishView, NotificationStreamView

urlpatterns = [
    path("stream/", NotificationStreamView.as_view(), name="notifications-stream"),
    path("publish/", NotificationPublishView.as_view(), name="notifications-publish"),
]
