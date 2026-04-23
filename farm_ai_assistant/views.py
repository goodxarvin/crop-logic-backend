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
from farm_hub.models import FarmHub
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


class FarmAccessMixin:
    @staticmethod
    def _get_farm(request, farm_uuid):
        if not farm_uuid:
            raise serializers.ValidationError({"farm_uuid": ["This field is required."]})
        return FarmAccessMixin._get_optional_farm(request, farm_uuid)

    @staticmethod
    def _get_optional_farm(request, farm_uuid):
        if not farm_uuid:
            return None
        try:
            return FarmHub.objects.get(farm_uuid=farm_uuid, owner=request.user)
        except FarmHub.DoesNotExist as exc:
            raise Http404("Farm not found") from exc

    @staticmethod
    def _farm_uuid_or_none(farm):
        return str(farm.farm_uuid) if farm else None


class ContextView(FarmAccessMixin, APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Farm AI Assistant"],
        parameters=[
            OpenApiParameter(name="farm_uuid", type=OpenApiTypes.UUID, location=OpenApiParameter.QUERY, required=False, default="11111111-1111-1111-1111-111111111111"),
        ],
        responses={200: status_response("FarmAiAssistantContextResponse", data=serializers.JSONField())},
    )
    def get(self, request):
        farm = self._get_optional_farm(request, request.query_params.get("farm_uuid"))
        data = deepcopy(CONTEXT_RESPONSE_DATA)
        data["farm_uuid"] = self._farm_uuid_or_none(farm)
        return Response(
            {"status": "success", "data": data},
            status=status.HTTP_200_OK,
        )


class ConversationAccessMixin(FarmAccessMixin):
    @staticmethod
    def _get_conversation(request, conversation_id, farm_uuid=None):
        filters = {"uuid": conversation_id, "owner": request.user}
        if farm_uuid:
            filters["farm__farm_uuid"] = farm_uuid
        else:
            filters["farm__isnull"] = True
        try:
            return Conversation.objects.select_related("farm").get(**filters)
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

    def _build_mock_assistant_payload(self, conversation):
        payload = deepcopy(CHAT_RESPONSE_DATA)
        payload["conversation_id"] = str(conversation.uuid)
        payload["farm_uuid"] = self._farm_uuid_or_none(conversation.farm)
        return payload

    def _get_or_create_conversation(self, request, validated):
        conversation_id = validated.get("conversation_id")
        farm_context = validated.get("farm_context")
        title = validated.get("title", "").strip()
        farm = self._get_optional_farm(request, validated.get("farm_uuid"))

        if conversation_id:
            conversation = self._get_conversation(
                request,
                conversation_id,
                farm.farm_uuid if farm else None,
            )
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
            farm=farm,
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
        if conversation.farm:
            payload["farm_uuid"] = str(conversation.farm.farm_uuid)
        if "farm_context" in validated:
            payload["farm_context"] = validated.get("farm_context") or {}
        if "title" in validated:
            payload["title"] = validated.get("title", "")
        return payload

    def _extract_assistant_payload(self, adapter_data, conversation):
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
            "conversation_id": str(conversation.uuid),
            "farm_uuid": self._farm_uuid_or_none(conversation.farm),
            "content": content,
            "sections": sections,
        }

    @staticmethod
    def _extract_task_submit_payload(adapter_data, conversation, message_id):
        payload_source = adapter_data
        if isinstance(adapter_data, dict) and isinstance(adapter_data.get("data"), dict):
            payload_source = adapter_data["data"]

        if not isinstance(payload_source, dict):
            payload_source = {}

        return {
            "task_id": str(payload_source.get("task_id") or ""),
            "status": str(payload_source.get("status") or ""),
            "status_url": str(payload_source.get("status_url") or ""),
            "conversation_id": str(conversation.uuid),
            "message_id": str(message_id),
            "farm_uuid": ConversationAccessMixin._farm_uuid_or_none(conversation.farm),
        }

    def _extract_task_status_payload(self, adapter_data, task_id, conversation=None, farm_uuid=None):
        payload_source = adapter_data
        if isinstance(adapter_data, dict) and isinstance(adapter_data.get("data"), dict):
            payload_source = adapter_data["data"]

        if not isinstance(payload_source, dict):
            payload_source = {}

        task_status_payload = {
            "task_id": str(payload_source.get("task_id") or task_id),
            "status": str(payload_source.get("status") or ""),
        }
        if conversation:
            task_status_payload["conversation_id"] = str(conversation.uuid)
            task_status_payload["farm_uuid"] = self._farm_uuid_or_none(conversation.farm)
        elif farm_uuid is not None:
            task_status_payload["farm_uuid"] = str(farm_uuid)

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

    def _extract_structured_task_result(self, adapter_data):
        payload_source = adapter_data
        if isinstance(adapter_data, dict) and isinstance(adapter_data.get("data"), dict):
            payload_source = adapter_data["data"]

        if not isinstance(payload_source, dict):
            return None

        result = payload_source.get("result")
        if isinstance(result, dict):
            return result

        if payload_source.get("status") == "SUCCESS":
            content = payload_source.get("content")
            sections = payload_source.get("sections")
            if content or sections:
                return {
                    "content": content or "",
                    "sections": sections or [],
                }

        return None

    @staticmethod
    def _serialize_chat_message(message):
        raw_response = message.raw_response if isinstance(message.raw_response, dict) else {}
        sections = raw_response.get("sections") if message.role == Message.ROLE_ASSISTANT else []
        return {
            "message_id": str(message.uuid),
            "conversation_id": str(message.conversation.uuid),
            "farm_uuid": ConversationAccessMixin._farm_uuid_or_none(message.farm),
            "role": message.role,
            "content": message.content,
            "sections": ConversationAccessMixin._normalize_sections(sections),
            "images": message.images if isinstance(message.images, list) else [],
            "created_at": message.created_at,
        }

    @staticmethod
    def _find_user_message_for_task(request, task_id, farm_uuid):
        filters = {
            "conversation__owner": request.user,
            "role": Message.ROLE_USER,
            "raw_response__task_id": task_id,
        }
        if farm_uuid:
            filters["farm__farm_uuid"] = farm_uuid
        else:
            filters["farm__isnull"] = True
        return (
            Message.objects.select_related("conversation", "farm")
            .filter(**filters)
            .order_by("-created_at")
            .first()
        )

    def _persist_task_result(self, user_message, task_id, result):
        assistant_payload = self._extract_assistant_payload(result, user_message.conversation)
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
                farm=user_message.farm,
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
        parameters=[
            OpenApiParameter(name="farm_uuid", type=OpenApiTypes.UUID, location=OpenApiParameter.QUERY, required=False, default="11111111-1111-1111-1111-111111111111"),
        ],
        responses={200: status_response("FarmAiAssistantConversationListResponse", data=ConversationSummarySerializer(many=True))},
    )
    def get(self, request):
        farm = self._get_optional_farm(request, request.query_params.get("farm_uuid"))
        conversations = (
            Conversation.objects.filter(owner=request.user, farm=farm)
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
        farm = self._get_optional_farm(request, validated.get("farm_uuid"))
        conversation = Conversation.objects.create(
            owner=request.user,
            farm=farm,
            title=validated.get("title", "").strip() or "New chat",
            farm_context=validated.get("farm_context") or {},
        )

        response_serializer = ConversationSummarySerializer(
            {
                "uuid": conversation.uuid,
                "farm": farm,
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
            OpenApiParameter(name="farm_uuid", type=OpenApiTypes.UUID, location=OpenApiParameter.QUERY, required=False, default="11111111-1111-1111-1111-111111111111"),
        ],
        responses={200: status_response("FarmAiAssistantMessageListResponse", data=ConversationMessagesSerializer())},
    )
    def get(self, request, conversation_id):
        farm = self._get_optional_farm(request, request.query_params.get("farm_uuid"))
        conversation = self._get_conversation(request, conversation_id, farm.farm_uuid if farm else None)
        messages = conversation.messages.select_related("farm").all()
        serialized_messages = [self._serialize_chat_message(message) for message in messages]
        return Response(
            {
                "status": "success",
                "data": {
                    "conversation_id": str(conversation.uuid),
                    "farm_uuid": self._farm_uuid_or_none(farm),
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
            OpenApiParameter(name="farm_uuid", type=OpenApiTypes.UUID, location=OpenApiParameter.QUERY, required=False, default="11111111-1111-1111-1111-111111111111"),
        ],
        responses={200: status_response("FarmAiAssistantConversationDeleteResponse", data=ConversationDeleteSerializer())},
    )
    def delete(self, request, conversation_id):
        farm = self._get_optional_farm(request, request.query_params.get("farm_uuid"))
        conversation = self._get_conversation(request, conversation_id, farm.farm_uuid if farm else None)
        deleted_conversation_id = str(conversation.uuid)
        deleted_farm_uuid = self._farm_uuid_or_none(conversation.farm)
        conversation.delete()
        return Response(
            {
                "status": "success",
                "data": {
                    "conversation_id": deleted_conversation_id,
                    "farm_uuid": deleted_farm_uuid,
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
            farm=conversation.farm,
            role=Message.ROLE_USER,
            content=validated.get("content", ""),
            images=validated.get("images", []),
            raw_response={"farm_uuid": self._farm_uuid_or_none(conversation.farm)},
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
            assistant_payload = self._extract_assistant_payload(adapter_response.data, conversation)
            response_status_code = adapter_response.status_code
        except ExternalAPIRequestError:
            assistant_payload = self._build_mock_assistant_payload(conversation)
            response_status_code = status.HTTP_200_OK

        assistant_message = Message.objects.create(
            conversation=conversation,
            farm=conversation.farm,
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
            farm=conversation.farm,
            role=Message.ROLE_USER,
            content=validated.get("content", ""),
            images=validated.get("images", []),
            raw_response={"farm_uuid": self._farm_uuid_or_none(conversation.farm)},
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
            conversation,
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
            OpenApiParameter(name="farm_uuid", type=OpenApiTypes.UUID, location=OpenApiParameter.QUERY, required=False, default="11111111-1111-1111-1111-111111111111"),
        ],
        responses={200: status_response("FarmAiAssistantChatTaskStatusResponse", data=ChatTaskStatusDataSerializer())},
    )
    def get(self, request, task_id):
        farm = self._get_optional_farm(request, request.query_params.get("farm_uuid"))
        try:
            query = {}
            if farm:
                query["farm_uuid"] = str(farm.farm_uuid)
            adapter_response = external_api_request(
                "ai",
                f"/tasks/{task_id}/status",
                method="GET",
                query=query,
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

        farm_uuid = farm.farm_uuid if farm else None
        user_message = self._find_user_message_for_task(request, task_id, farm_uuid)
        conversation = user_message.conversation if user_message else None
        task_status_payload = self._extract_task_status_payload(
            adapter_response.data,
            task_id,
            conversation=conversation,
            farm_uuid=farm_uuid,
        )

        result = self._extract_structured_task_result(adapter_response.data)
        if result is not None:
            task_status_payload["result"] = result

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
