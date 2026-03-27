from django.urls import path

from .views import (
    ChatDetailView,
    ChatListCreateView,
    ChatMessagesView,
    ChatTaskCreateView,
    ChatTaskStatusView,
    ChatView,
    ContextView,
)

urlpatterns = [
    path("context/", ContextView.as_view(), name="farm-ai-assistant-context"),
    path("chat/", ChatView.as_view(), name="farm-ai-assistant-chat"),
    path("chat/task/", ChatTaskCreateView.as_view(), name="farm-ai-assistant-chat-task-create"),
    path("chat/task/<str:task_id>/status/", ChatTaskStatusView.as_view(), name="farm-ai-assistant-chat-task-status"),
    path("chats/", ChatListCreateView.as_view(), name="farm-ai-assistant-chat-list-create"),
    path("chats/<uuid:conversation_id>/", ChatDetailView.as_view(), name="farm-ai-assistant-chat-detail"),
    path("chats/<uuid:conversation_id>/messages/", ChatMessagesView.as_view(), name="farm-ai-assistant-chat-messages"),
]
