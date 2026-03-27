"""Farm AI Assistant API views."""

from copy import deepcopy

from django.db.models import Count
from django.http import Http404
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from config.swagger import status_response
from external_api_adapter import request as external_api_request
from external_api_adapter.exceptions import ExternalAPIRequestError
from .mock_data import CHAT_RESPONSE_DATA, CONTEXT_RESPONSE_DATA
from .models import Conversation, Message
from .serializers import (
    ChatPostSerializer,
    ChatResponseDataSerializer,
    ConversationCreateSerializer,
    ConversationDeleteSerializer,
    ConversationMessagesSerializer,
    ConversationSummarySerializer,
)


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


class ConversationAccessMixin:
    @staticmethod
    def _get_conversation(request, conversation_id):
        try:
            return Conversation.objects.get(uuid=conversation_id, owner=request.user)
        except Conversation.DoesNotExist as exc:
            raise Http404("Conversation not found") from exc

    @staticmethod
    def _normalize_sections(raw_sections):
        if not isinstance(raw_sections, list):
            return []

        allowed_keys = {
            "type",
            "title",
            "content",
            "items",
            "icon",
            "frequency",
            "amount",
            "timing",
            "expandableExplanation",
        }
        normalized_sections = []
        for section in raw_sections:
            if not isinstance(section, dict) or not section.get("type"):
                continue

            normalized_section = {}
            for key in allowed_keys:
                value = section.get(key)
                if value is None:
                    continue
                if key == "items":
                    if not isinstance(value, list):
                        continue
                    normalized_section[key] = [str(item) for item in value]
                    continue
                normalized_section[key] = str(value) if key != "type" else value

            normalized_sections.append(normalized_section)
        return normalized_sections

    def _build_mock_assistant_payload(self, conversation_id):
        payload = deepcopy(CHAT_RESPONSE_DATA)
        payload["conversation_id"] = str(conversation_id)
        return payload

    def _extract_assistant_payload(self, adapter_data, conversation_id):
        payload_source = adapter_data
        if isinstance(adapter_data, dict) and isinstance(adapter_data.get("data"), dict):
            payload_source = adapter_data["data"]

        content = ""
        sections = []

        if isinstance(payload_source, dict):
            content = payload_source.get("content") or ""
            sections = self._normalize_sections(payload_source.get("sections"))

        if not sections and isinstance(adapter_data, dict):
            sections = self._normalize_sections(adapter_data.get("sections"))

        if not content and isinstance(adapter_data, dict):
            content = adapter_data.get("body") or adapter_data.get("content") or ""

        return {
            "message_id": "",
            "conversation_id": str(conversation_id),
            "content": content,
            "sections": sections,
        }

    @staticmethod
    def _serialize_chat_message(message):
        raw_response = message.raw_response if isinstance(message.raw_response, dict) else {}
        sections = raw_response.get("sections") if message.role == Message.ROLE_ASSISTANT else []
        return {
            "message_id": str(message.uuid),
            "conversation_id": str(message.conversation.uuid),
            "role": message.role,
            "content": message.content,
            "sections": ConversationAccessMixin._normalize_sections(sections),
            "images": message.images if isinstance(message.images, list) else [],
            "created_at": message.created_at,
        }


class ChatListCreateView(ConversationAccessMixin, APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Farm AI Assistant"],
        responses={200: status_response("FarmAiAssistantConversationListResponse", data=ConversationSummarySerializer(many=True))},
    )
    def get(self, request):
        conversations = (
            Conversation.objects.filter(owner=request.user)
            .annotate(message_count=Count("messages"))
            .order_by("-updated_at", "-created_at")
        )
        serializer = ConversationSummarySerializer(conversations, many=True)
        return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Farm AI Assistant"],
        request=ConversationCreateSerializer,
        responses={201: status_response("FarmAiAssistantConversationCreateResponse", data=ConversationSummarySerializer())},
    )
    def post(self, request):
        serializer = ConversationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated = serializer.validated_data
        conversation = Conversation.objects.create(
            owner=request.user,
            title=validated.get("title", "").strip() or "New chat",
            farm_context=validated.get("farm_context") or {},
        )

        response_serializer = ConversationSummarySerializer(
            {
                "uuid": conversation.uuid,
                "message_count": 0,
            }
        )
        return Response({"status": "success", "data": response_serializer.data}, status=status.HTTP_201_CREATED)


class ChatMessagesView(ConversationAccessMixin, APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Farm AI Assistant"],
        parameters=[
            OpenApiParameter(name="conversation_id", type=OpenApiTypes.UUID, location=OpenApiParameter.PATH),
        ],
        responses={200: status_response("FarmAiAssistantMessageListResponse", data=ConversationMessagesSerializer())},
    )
    def get(self, request, conversation_id):
        conversation = self._get_conversation(request, conversation_id)
        messages = conversation.messages.all()
        serialized_messages = [self._serialize_chat_message(message) for message in messages]
        return Response(
            {
                "status": "success",
                "data": {
                    "conversation_id": str(conversation.uuid),
                    "messages": serialized_messages,
                },
            },
            status=status.HTTP_200_OK,
        )


class ChatDetailView(ConversationAccessMixin, APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Farm AI Assistant"],
        parameters=[
            OpenApiParameter(name="conversation_id", type=OpenApiTypes.UUID, location=OpenApiParameter.PATH),
        ],
        responses={200: status_response("FarmAiAssistantConversationDeleteResponse", data=ConversationDeleteSerializer())},
    )
    def delete(self, request, conversation_id):
        conversation = self._get_conversation(request, conversation_id)
        deleted_conversation_id = str(conversation.uuid)
        conversation.delete()
        return Response(
            {
                "status": "success",
                "data": {
                    "conversation_id": deleted_conversation_id,
                },
            },
            status=status.HTTP_200_OK,
        )


class ChatView(ConversationAccessMixin, APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Farm AI Assistant"],
        request=ChatPostSerializer,
        responses={200: status_response("FarmAiAssistantChatResponse", data=ChatResponseDataSerializer())},
    )
    def post(self, request):
        serializer = ChatPostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated = serializer.validated_data
        conversation_id = validated.get("conversation_id")
        farm_context = validated.get("farm_context")
        title = validated.get("title", "").strip()

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
                title=title or (validated.get("content", "")[:255]) or "New chat",
                farm_context=farm_context or {},
            )

        user_message = Message.objects.create(
            conversation=conversation,
            role=Message.ROLE_USER,
            content=validated.get("content", ""),
            images=validated.get("images", []),
            raw_response={},
        )

        adapter_payload = dict(request.data)
        adapter_payload["conversation_id"] = str(conversation.uuid)

        try:
            adapter_response = external_api_request(
                "ai",
                "/rag/chat",
                method="POST",
                payload=adapter_payload,
            )
            if adapter_response.status_code >= 400:
                return Response(
                    {
                        "status": "error",
                        "data": adapter_response.data,
                    },
                    status=adapter_response.status_code,
                )
            assistant_payload = self._extract_assistant_payload(adapter_response.data, conversation.uuid)
            response_status_code = adapter_response.status_code
        except ExternalAPIRequestError:
            assistant_payload = self._build_mock_assistant_payload(conversation.uuid)
            response_status_code = status.HTTP_200_OK

        assistant_message = Message.objects.create(
            conversation=conversation,
            role=Message.ROLE_ASSISTANT,
            content=assistant_payload.get("content", ""),
            raw_response={},
        )
        assistant_payload["message_id"] = str(assistant_message.uuid)
        assistant_message.raw_response = assistant_payload
        assistant_message.save(update_fields=["raw_response"])

        if not conversation.title:
            conversation.title = (validated.get("content", "") or assistant_payload.get("content", "") or "New chat")[:255]
            conversation.save(update_fields=["title", "updated_at"])
        else:
            conversation.save(update_fields=["updated_at"])

        return Response(
            {
                "status": "success",
                "data": assistant_payload,
            },
            status=response_status_code,
        )
