from django.urls import path

from .views import  NotificationLongPollView, NotificationMarkReadView

urlpatterns = [
    path("long-poll/", NotificationLongPollView.as_view(), name="notification-long-poll"),
    path("mark-as-read/", NotificationMarkReadView.as_view(), name="notification-mark-as-read"),
]
