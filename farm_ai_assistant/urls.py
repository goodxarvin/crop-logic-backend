from django.urls import path

from .views import ChatListView, ChatMessagesView, ChatView, ContextView

urlpatterns = [
    path("context/", ContextView.as_view(), name="farm-ai-assistant-context"),
    path("chat/", ChatView.as_view(), name="farm-ai-assistant-chat"),
    path("chats/", ChatListView.as_view(), name="farm-ai-assistant-chat-list"),
    path("chats/<uuid:conversation_id>/messages/", ChatMessagesView.as_view(), name="farm-ai-assistant-chat-messages"),
]
