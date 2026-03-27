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
    ChatTaskStatusDataSerializer,
    ChatTaskSubmitDataSerializer,
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

    def _get_or_create_conversation(self, request, validated):
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
            return conversation

        return Conversation.objects.create(
            owner=request.user,
            title=title or (validated.get("content", "")[:255]) or "New chat",
            farm_context=farm_context or {},
        )

    @staticmethod
    def _build_adapter_payload(request, validated, conversation):
        payload = {
            "content": validated.get("content", ""),
            "query": validated.get("content", ""),
            "images": validated.get("images", []),
            "conversation_id": str(conversation.uuid),
            "user_id": request.user.id,
        }
        if "farm_context" in validated:
            payload["farm_context"] = validated.get("farm_context") or {}
        if "title" in validated:
            payload["title"] = validated.get("title", "")
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
    def _extract_task_submit_payload(adapter_data, conversation_id, message_id):
        payload_source = adapter_data
        if isinstance(adapter_data, dict) and isinstance(adapter_data.get("data"), dict):
            payload_source = adapter_data["data"]

        if not isinstance(payload_source, dict):
            payload_source = {}

        return {
            "task_id": str(payload_source.get("task_id") or ""),
            "status": str(payload_source.get("status") or ""),
            "status_url": str(payload_source.get("status_url") or ""),
            "conversation_id": str(conversation_id),
            "message_id": str(message_id),
        }

    def _extract_task_status_payload(self, adapter_data, task_id, conversation_id=None):
        payload_source = adapter_data
        if isinstance(adapter_data, dict) and isinstance(adapter_data.get("data"), dict):
            payload_source = adapter_data["data"]

        if not isinstance(payload_source, dict):
            payload_source = {}

        task_status_payload = {
            "task_id": str(payload_source.get("task_id") or task_id),
            "status": str(payload_source.get("status") or ""),
        }
        if conversation_id:
            task_status_payload["conversation_id"] = str(conversation_id)

        progress = payload_source.get("progress")
        if progress is not None:
            task_status_payload["progress"] = progress
        elif payload_source.get("message") and task_status_payload["status"] != "SUCCESS":
            task_status_payload["progress"] = {"message": payload_source.get("message")}

        if payload_source.get("error"):
            task_status_payload["error"] = str(payload_source["error"])

        result = payload_source.get("result")
        if result is not None:
            task_status_payload["result"] = result

        return task_status_payload

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

    @staticmethod
    def _find_user_message_for_task(request, task_id):
        return (
            Message.objects.select_related("conversation")
            .filter(
                conversation__owner=request.user,
                role=Message.ROLE_USER,
                raw_response__task_id=task_id,
            )
            .order_by("-created_at")
            .first()
        )

    def _persist_task_result(self, user_message, task_id, result):
        assistant_payload = self._extract_assistant_payload(result, user_message.conversation.uuid)
        assistant_message = (
            user_message.conversation.messages.filter(
                role=Message.ROLE_ASSISTANT,
                raw_response__task_id=task_id,
            )
            .order_by("-created_at")
            .first()
        )

        if assistant_message is None:
            assistant_message = Message.objects.create(
                conversation=user_message.conversation,
                role=Message.ROLE_ASSISTANT,
                content=assistant_payload.get("content", ""),
                raw_response={},
            )

        assistant_payload["message_id"] = str(assistant_message.uuid)
        assistant_payload["task_id"] = task_id
        assistant_message.content = assistant_payload.get("content", "")
        assistant_message.raw_response = assistant_payload
        assistant_message.save(update_fields=["content", "raw_response"])

        conversation = user_message.conversation
        if not conversation.title:
            conversation.title = (
                user_message.content or assistant_payload.get("content", "") or "New chat"
            )[:255]
            conversation.save(update_fields=["title", "updated_at"])
        else:
            conversation.save(update_fields=["updated_at"])

        return assistant_payload


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
        conversation = self._get_or_create_conversation(request, validated)

        user_message = Message.objects.create(
            conversation=conversation,
            role=Message.ROLE_USER,
            content=validated.get("content", ""),
            images=validated.get("images", []),
            raw_response={},
        )

        adapter_payload = self._build_adapter_payload(request, validated, conversation)

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


class ChatTaskCreateView(ConversationAccessMixin, APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Farm AI Assistant"],
        request=ChatPostSerializer,
        responses={202: status_response("FarmAiAssistantChatTaskCreateResponse", data=ChatTaskSubmitDataSerializer())},
    )
    def post(self, request):
        serializer = ChatPostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated = serializer.validated_data
        conversation = self._get_or_create_conversation(request, validated)
        user_message = Message.objects.create(
            conversation=conversation,
            role=Message.ROLE_USER,
            content=validated.get("content", ""),
            images=validated.get("images", []),
            raw_response={},
        )

        adapter_payload = self._build_adapter_payload(request, validated, conversation)
        try:
            adapter_response = external_api_request(
                "ai",
                "/rag/chat/generate",
                method="POST",
                payload=adapter_payload,
            )
        except ExternalAPIRequestError:
            return Response(
                {
                    "status": "error",
                    "data": {
                        "message": "External AI service is unavailable.",
                    },
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if adapter_response.status_code >= 400:
            return Response(
                {
                    "status": "error",
                    "data": adapter_response.data,
                },
                status=adapter_response.status_code,
            )

        task_payload = self._extract_task_submit_payload(
            adapter_response.data,
            conversation.uuid,
            user_message.uuid,
        )
        user_message.raw_response = task_payload
        user_message.save(update_fields=["raw_response"])
        conversation.save(update_fields=["updated_at"])

        return Response(
            {
                "status": "success",
                "data": task_payload,
            },
            status=adapter_response.status_code,
        )


class ChatTaskStatusView(ConversationAccessMixin, APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Farm AI Assistant"],
        parameters=[
            OpenApiParameter(name="task_id", type=OpenApiTypes.STR, location=OpenApiParameter.PATH),
        ],
        responses={200: status_response("FarmAiAssistantChatTaskStatusResponse", data=ChatTaskStatusDataSerializer())},
    )
    def get(self, request, task_id):
        try:
            adapter_response = external_api_request(
                "ai",
                f"/tasks/{task_id}/status",
                method="GET",
            )
        except ExternalAPIRequestError:
            return Response(
                {
                    "status": "error",
                    "data": {
                        "message": "External AI service is unavailable.",
                    },
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if adapter_response.status_code >= 400:
            return Response(
                {
                    "status": "error",
                    "data": adapter_response.data,
                },
                status=adapter_response.status_code,
            )

        user_message = self._find_user_message_for_task(request, task_id)
        conversation_id = user_message.conversation.uuid if user_message else None
        task_status_payload = self._extract_task_status_payload(
            adapter_response.data,
            task_id,
            conversation_id=conversation_id,
        )

        result = task_status_payload.get("result")
        if user_message and task_status_payload.get("status") == "SUCCESS" and isinstance(result, dict):
            assistant_payload = self._persist_task_result(user_message, task_id, result)
            task_status_payload["result"] = assistant_payload

        return Response(
            {
                "status": "success",
                "data": task_status_payload,
            },
            status=adapter_response.status_code,
        )
