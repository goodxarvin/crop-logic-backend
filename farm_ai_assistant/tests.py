from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory, force_authenticate

from .models import Conversation, Message
from .views import ChatTaskStatusView


@override_settings(USE_EXTERNAL_API_MOCK=True)
class ChatTaskStatusViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            username="farmer",
            password="secret123",
            email="farmer@example.com",
            phone_number="09120000000",
        )
        self.conversation = Conversation.objects.create(
            owner=self.user,
            title="Irrigation chat",
            farm_context={},
        )
        self.user_message = Message.objects.create(
            conversation=self.conversation,
            role=Message.ROLE_USER,
            content="What is the best irrigation plan?",
            raw_response={
                "task_id": "farm-ai-chat-task-123",
                "status": "PENDING",
                "status_url": "/api/tasks/farm-ai-chat-task-123/status/",
            },
        )

    def test_status_success_uses_chat_mock_result_and_persists_assistant_message(self):
        request = self.factory.get("/api/farm-ai-assistant/chat/task/farm-ai-chat-task-123/status/")
        force_authenticate(request, user=self.user)

        response = ChatTaskStatusView.as_view()(request, task_id="farm-ai-chat-task-123")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["data"]["task_id"], "farm-ai-chat-task-123")
        self.assertEqual(response.data["data"]["status"], "SUCCESS")
        self.assertEqual(response.data["data"]["conversation_id"], str(self.conversation.uuid))
        self.assertEqual(response.data["data"]["result"]["content"], "Here is the recommended plan.")
        self.assertEqual(len(response.data["data"]["result"]["sections"]), 3)
        self.assertEqual(response.data["data"]["result"]["task_id"], "farm-ai-chat-task-123")

        assistant_message = (
            self.conversation.messages.filter(role=Message.ROLE_ASSISTANT)
            .order_by("-created_at")
            .first()
        )
        self.assertIsNotNone(assistant_message)
        self.assertEqual(assistant_message.content, "Here is the recommended plan.")
        self.assertEqual(assistant_message.raw_response["task_id"], "farm-ai-chat-task-123")
        self.assertEqual(len(assistant_message.raw_response["sections"]), 3)
