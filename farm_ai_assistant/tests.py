from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory, force_authenticate

from farm_hub.models import FarmHub, FarmType

from .models import Conversation, Message
from .views import (
    ChatDetailView,
    ChatListCreateView,
    ChatMessagesView,
    ChatTaskCreateView,
    ChatTaskStatusView,
    ContextView,
)


@override_settings(USE_EXTERNAL_API_MOCK=True)
class FarmAiAssistantOptionalFarmUuidTests(TestCase):
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

    def test_context_allows_missing_farm_uuid(self):
        request = self.factory.get("/api/farm-ai-assistant/context/")
        force_authenticate(request, user=self.user)

        response = ContextView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "success")
        self.assertIsNone(response.data["data"]["farm_uuid"])

    def test_chat_task_create_allows_missing_farm_uuid_for_landing_chat(self):
        request = self.factory.post(
            "/api/farm-ai-assistant/chat/task/",
            {"content": "Give me a landing page recommendation"},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = ChatTaskCreateView.as_view()(request)

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["data"]["task_id"], "farm-ai-chat-task-123")
        self.assertIsNone(response.data["data"]["farm_uuid"])

        conversation = Conversation.objects.get(uuid=response.data["data"]["conversation_id"])
        self.assertIsNone(conversation.farm)
        self.assertEqual(conversation.owner_id, self.user.id)

        user_message = conversation.messages.get(role=Message.ROLE_USER)
        self.assertIsNone(user_message.farm)
        self.assertIsNone(user_message.raw_response["farm_uuid"])

    def test_status_success_without_farm_uuid_persists_assistant_message(self):
        conversation = Conversation.objects.create(
            owner=self.user,
            farm=None,
            title="Landing chat",
            farm_context={},
        )
        Message.objects.create(
            conversation=conversation,
            farm=None,
            role=Message.ROLE_USER,
            content="What should I plant?",
            raw_response={
                "task_id": "farm-ai-chat-task-123",
                "status": "PENDING",
                "status_url": "/api/tasks/farm-ai-chat-task-123/status/",
                "farm_uuid": None,
            },
        )

        request = self.factory.get("/api/farm-ai-assistant/chat/task/farm-ai-chat-task-123/status/")
        force_authenticate(request, user=self.user)

        response = ChatTaskStatusView.as_view()(request, task_id="farm-ai-chat-task-123")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["data"]["task_id"], "farm-ai-chat-task-123")
        self.assertEqual(response.data["data"]["status"], "SUCCESS")
        self.assertEqual(response.data["data"]["conversation_id"], str(conversation.uuid))
        self.assertIsNone(response.data["data"]["farm_uuid"])
        self.assertEqual(response.data["data"]["result"]["content"], "Here is the recommended plan.")
        self.assertEqual(response.data["data"]["result"]["task_id"], "farm-ai-chat-task-123")

        assistant_message = (
            conversation.messages.filter(role=Message.ROLE_ASSISTANT)
            .order_by("-created_at")
            .first()
        )
        self.assertIsNotNone(assistant_message)
        self.assertIsNone(assistant_message.farm)
        self.assertEqual(assistant_message.content, "Here is the recommended plan.")
        self.assertIsNone(assistant_message.raw_response["farm_uuid"])
        self.assertEqual(assistant_message.raw_response["task_id"], "farm-ai-chat-task-123")

    def test_status_success_with_farm_uuid_still_works_for_farm_chat(self):
        conversation = Conversation.objects.create(
            owner=self.user,
            farm=self.farm,
            title="Farm chat",
            farm_context={},
        )
        Message.objects.create(
            conversation=conversation,
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

        request = self.factory.get(
            f"/api/farm-ai-assistant/chat/task/farm-ai-chat-task-123/status/?farm_uuid={self.farm.farm_uuid}"
        )
        force_authenticate(request, user=self.user)

        response = ChatTaskStatusView.as_view()(request, task_id="farm-ai-chat-task-123")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["conversation_id"], str(conversation.uuid))
        self.assertEqual(response.data["data"]["farm_uuid"], str(self.farm.farm_uuid))

    def test_chat_list_create_messages_and_delete_work_without_farm_uuid(self):
        landing_conversation = Conversation.objects.create(
            owner=self.user,
            farm=None,
            title="Landing chat",
            farm_context={"source": "landing"},
        )
        Message.objects.create(
            conversation=landing_conversation,
            farm=None,
            role=Message.ROLE_USER,
            content="Hello from landing",
            raw_response={"farm_uuid": None},
        )
        farm_conversation = Conversation.objects.create(
            owner=self.user,
            farm=self.farm,
            title="Farm chat",
            farm_context={},
        )
        Message.objects.create(
            conversation=farm_conversation,
            farm=self.farm,
            role=Message.ROLE_USER,
            content="Hello from farm",
            raw_response={"farm_uuid": str(self.farm.farm_uuid)},
        )

        list_request = self.factory.get("/api/farm-ai-assistant/chats/")
        force_authenticate(list_request, user=self.user)
        list_response = ChatListCreateView.as_view()(list_request)

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.data["data"]), 1)
        self.assertEqual(list_response.data["data"][0]["id"], str(landing_conversation.uuid))
        self.assertIsNone(list_response.data["data"][0]["farm_uuid"])

        create_request = self.factory.post(
            "/api/farm-ai-assistant/chats/",
            {"title": "New landing conversation"},
            format="json",
        )
        force_authenticate(create_request, user=self.user)
        create_response = ChatListCreateView.as_view()(create_request)

        self.assertEqual(create_response.status_code, 201)
        self.assertIsNone(create_response.data["data"]["farm_uuid"])

        created_conversation = Conversation.objects.get(uuid=create_response.data["data"]["id"])
        self.assertIsNone(created_conversation.farm)

        messages_request = self.factory.get(
            f"/api/farm-ai-assistant/chats/{landing_conversation.uuid}/messages/"
        )
        force_authenticate(messages_request, user=self.user)
        messages_response = ChatMessagesView.as_view()(
            messages_request,
            conversation_id=landing_conversation.uuid,
        )

        self.assertEqual(messages_response.status_code, 200)
        self.assertEqual(messages_response.data["data"]["conversation_id"], str(landing_conversation.uuid))
        self.assertIsNone(messages_response.data["data"]["farm_uuid"])
        self.assertEqual(len(messages_response.data["data"]["messages"]), 1)
        self.assertIsNone(messages_response.data["data"]["messages"][0]["farm_uuid"])

        delete_request = self.factory.delete(f"/api/farm-ai-assistant/chats/{landing_conversation.uuid}/")
        force_authenticate(delete_request, user=self.user)
        delete_response = ChatDetailView.as_view()(
            delete_request,
            conversation_id=landing_conversation.uuid,
        )

        self.assertEqual(delete_response.status_code, 200)
        self.assertEqual(delete_response.data["data"]["conversation_id"], str(landing_conversation.uuid))
        self.assertIsNone(delete_response.data["data"]["farm_uuid"])
        self.assertFalse(Conversation.objects.filter(uuid=landing_conversation.uuid).exists())
