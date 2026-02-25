from django.urls import path

from .views import ChatView, ContextView

urlpatterns = [
    path("context/", ContextView.as_view(), name="farm-ai-assistant-context"),
    path("chat/", ChatView.as_view(), name="farm-ai-assistant-chat"),
]
