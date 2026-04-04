from django.urls import path

from .views import  NotificationLongPollView

urlpatterns = [
    path("long-poll/", NotificationLongPollView.as_view(), name="notification-long-poll"),
]
