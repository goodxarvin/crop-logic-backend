"""Farm AI Assistant API views."""

from django.db.models import Count, OuterRef, Subquery
from django.http import Http404, HttpResponse
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from config.swagger import status_response
from external_api_adapter import request as external_api_request
from .mock_data import CONTEXT_RESPONSE_DATA
from .models import Conversation, Message
from .serializers import ChatPostSerializer, ConversationListSerializer, MessageSerializer


class ContextView(APIView):
    @extend_schema(
        tags=["Farm AI Assistant"],
        responses={200: status_response("FarmAiAssistantContextResponse", data=serializers.JSONField())},
    )
    def get(self, request):
        return Response(
            {"status": "success", "data": CONTEXT_RESPONSE_DATA},
            status=status.HTTP_200_OK,
        )


class ChatListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Farm AI Assistant"],
        responses={200: status_response("FarmAiAssistantConversationListResponse", data=ConversationListSerializer(many=True))},
    )
    def get(self, request):
        last_message_subquery = Message.objects.filter(conversation=OuterRef("pk")).order_by("-created_at", "-id")
        conversations = (
            Conversation.objects.filter(owner=request.user)
            .annotate(
                message_count=Count("messages"),
                last_message=Subquery(last_message_subquery.values("content")[:1]),
            )
            .order_by("-updated_at", "-created_at")
        )

        serializer = ConversationListSerializer(conversations, many=True)
        return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)


class ChatMessagesView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_conversation(self, request, conversation_id):
        try:
            return Conversation.objects.get(uuid=conversation_id, owner=request.user)
        except Conversation.DoesNotExist as exc:
            raise Http404("Conversation not found") from exc

    @extend_schema(
        tags=["Farm AI Assistant"],
        parameters=[
            OpenApiParameter(name="conversation_id", type=OpenApiTypes.UUID, location=OpenApiParameter.PATH),
        ],
        responses={200: status_response("FarmAiAssistantMessageListResponse", data=MessageSerializer(many=True))},
    )
    def get(self, request, conversation_id):
        conversation = self._get_conversation(request, conversation_id)
        messages = conversation.messages.all()
        serializer = MessageSerializer(messages, many=True)
        return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)


class ChatView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_conversation(self, request, conversation_id):
        try:
            return Conversation.objects.get(uuid=conversation_id, owner=request.user)
        except Conversation.DoesNotExist as exc:
            raise Http404("Conversation not found") from exc

    @extend_schema(
        tags=["Farm AI Assistant"],
        responses={200: status_response("FarmAiAssistantConversationListAliasResponse", data=ConversationListSerializer(many=True))},
    )
    def get(self, request):
        return ChatListView().get(request)

    @extend_schema(
        tags=["Farm AI Assistant"],
        request=ChatPostSerializer,
        responses={200: status_response("FarmAiAssistantChatResponse", data=serializers.JSONField())},
    )
    def post(self, request):
        serializer = ChatPostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated = serializer.validated_data
        conversation_id = validated.get("conversation_id")
        farm_context = validated.get("farm_context")
        title = validated.get("title", "")

        if conversation_id:
            conversation = self._get_conversation(request, conversation_id)
            updated_fields = []
            if farm_context is not None:
                conversation.farm_context = farm_context
                updated_fields.append("farm_context")
            if title:
                conversation.title = title
                updated_fields.append("title")
            if updated_fields:
                updated_fields.append("updated_at")
                conversation.save(update_fields=updated_fields)
        else:
            conversation = Conversation.objects.create(
                owner=request.user,
                title=title or (validated.get("content", "")[:255]),
                farm_context=farm_context or {},
            )

        user_message = Message.objects.create(
            conversation=conversation,
            role=Message.ROLE_USER,
            content=validated.get("content", ""),
            images=validated.get("images", []),
        )

        adapter_payload = dict(request.data)
        adapter_payload["conversation_id"] = str(conversation.uuid)
        adapter_response = external_api_request(
            "ai",
            "/rag/chat",
            method="POST",
            payload=adapter_payload,
        )

        if isinstance(adapter_response.data, dict) and "body" in adapter_response.data:
            conversation.save(update_fields=["updated_at"])
            return HttpResponse(
                adapter_response.data["body"],
                status=adapter_response.status_code,
                content_type=adapter_response.data.get("content_type", "text/plain; charset=utf-8"),
            )

        assistant_content = ""
        if isinstance(adapter_response.data, dict):
            assistant_content = adapter_response.data.get("content") or ""
            if not assistant_content and isinstance(adapter_response.data.get("data"), dict):
                assistant_content = adapter_response.data["data"].get("content") or ""

        assistant_message = Message.objects.create(
            conversation=conversation,
            role=Message.ROLE_ASSISTANT,
            content=assistant_content,
            raw_response=adapter_response.data if isinstance(adapter_response.data, dict) else {"body": str(adapter_response.data)},
        )

        if not conversation.title:
            conversation.title = (validated.get("content", "") or assistant_content or "New chat")[:255]
            conversation.save(update_fields=["title", "updated_at"])
        else:
            conversation.save(update_fields=["updated_at"])

        response_data = adapter_response.data
        if isinstance(response_data, dict):
            data = response_data.get("data")
            if isinstance(data, dict):
                data.setdefault("conversation_id", str(conversation.uuid))
                data.setdefault("user_message_id", str(user_message.uuid))
                data.setdefault("assistant_message_id", str(assistant_message.uuid))
            else:
                response_data = {
                    "conversation_id": str(conversation.uuid),
                    "user_message_id": str(user_message.uuid),
                    "assistant_message_id": str(assistant_message.uuid),
                    "response": response_data,
                }
        else:
            response_data = {
                "conversation_id": str(conversation.uuid),
                "user_message_id": str(user_message.uuid),
                "assistant_message_id": str(assistant_message.uuid),
                "response": response_data,
            }

        return Response(response_data, status=adapter_response.status_code)
