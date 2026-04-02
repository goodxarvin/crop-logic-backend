from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory, force_authenticate

from farm_hub.models import FarmHub, FarmType

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
        self.farm_type, _ = FarmType.objects.get_or_create(name="زراعی")
        self.farm = FarmHub.objects.create(
            owner=self.user,
            farm_type=self.farm_type,
            name="Farm 1",
        )
        self.conversation = Conversation.objects.create(
            owner=self.user,
            farm=self.farm,
            title="Irrigation chat",
            farm_context={},
        )
        self.user_message = Message.objects.create(
            conversation=self.conversation,
            farm=self.farm,
            role=Message.ROLE_USER,
            content="What is the best irrigation plan?",
            raw_response={
                "task_id": "farm-ai-chat-task-123",
                "status": "PENDING",
                "status_url": "/api/tasks/farm-ai-chat-task-123/status/",
                "farm_uuid": str(self.farm.farm_uuid),
            },
        )

    def test_status_success_uses_chat_mock_result_and_persists_assistant_message(self):
        request = self.factory.get(
            f"/api/farm-ai-assistant/chat/task/farm-ai-chat-task-123/status/?farm_uuid={self.farm.farm_uuid}"
        )
        force_authenticate(request, user=self.user)

        response = ChatTaskStatusView.as_view()(request, task_id="farm-ai-chat-task-123")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["data"]["task_id"], "farm-ai-chat-task-123")
        self.assertEqual(response.data["data"]["status"], "SUCCESS")
        self.assertEqual(response.data["data"]["conversation_id"], str(self.conversation.uuid))
        self.assertEqual(response.data["data"]["farm_uuid"], str(self.farm.farm_uuid))
        self.assertEqual(response.data["data"]["result"]["content"], "Here is the recommended plan.")
        self.assertEqual(len(response.data["data"]["result"]["sections"]), 3)
        self.assertEqual(response.data["data"]["result"]["task_id"], "farm-ai-chat-task-123")

        assistant_message = (
            self.conversation.messages.filter(role=Message.ROLE_ASSISTANT)
            .order_by("-created_at")
            .first()
        )
        self.assertIsNotNone(assistant_message)
        self.assertEqual(assistant_message.farm_id, self.farm.id)
        self.assertEqual(assistant_message.content, "Here is the recommended plan.")
        self.assertEqual(assistant_message.raw_response["task_id"], "farm-ai-chat-task-123")
        self.assertEqual(assistant_message.raw_response["farm_uuid"], str(self.farm.farm_uuid))
        self.assertEqual(len(assistant_message.raw_response["sections"]), 3)
