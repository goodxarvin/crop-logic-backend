from django.urls import path

from .views import NotificationListView, NotificationLongPollView, NotificationMarkReadView

urlpatterns = [
    path("list/", NotificationListView.as_view(), name="notification-list"),
    path("long-poll/", NotificationLongPollView.as_view(), name="notification-long-poll"),
    path("mark-as-read/", NotificationMarkReadView.as_view(), name="notification-mark-as-read"),
]
