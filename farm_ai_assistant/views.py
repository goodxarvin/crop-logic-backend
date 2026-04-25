"""Farm AI Assistant API views."""

import json
from copy import deepcopy

from django.db.models import Count
from django.http import Http404
from rest_framework import serializers, status
from rest_framework.exceptions import ParseError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from config.swagger import status_response
from external_api_adapter import request as external_api_request
from external_api_adapter.exceptions import ExternalAPIRequestError
from farm_hub.models import FarmHub
from .mock_data import CONTEXT_RESPONSE_DATA
from .models import Conversation, Message
from .serializers import (
    ChatPostSerializer,
    ChatResponseDataSerializer,
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
    def _generate_conversation_title(query):
        normalized_query = (query or "").strip()
        if not normalized_query:
            return "Image"
        first_word = normalized_query.split()[0].strip()
        return (first_word or normalized_query or "New chat")[:255]

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
            "primaryAction",
            "frequency",
            "amount",
            "timing",
            "validityPeriod",
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

    def _get_or_create_conversation(self, request, validated):
        conversation_id = validated.get("conversation_id")
        farm = self._get_optional_farm(request, validated.get("farm_uuid"))

        if conversation_id:
            conversation = self._get_conversation(
                request,
                conversation_id,
                farm.farm_uuid if farm else None,
            )
            return conversation

        return Conversation.objects.create(
            owner=request.user,
            farm=farm,
            title=self._generate_conversation_title(validated.get("query", "")),
            farm_context={},
        )

    @staticmethod
    def _serialize_history_messages(history):
        normalized_history = []
        for item in history or []:
            if not isinstance(item, dict):
                continue
            role = str(item.get("role") or "").strip()
            content = str(item.get("content") or item.get("message") or "").strip()
            if not role and not content:
                continue
            normalized_item = {}
            if role:
                normalized_item["role"] = role
            if content:
                normalized_item["content"] = content
            if item.get("sections") is not None:
                normalized_item["sections"] = item.get("sections")
            normalized_history.append(normalized_item)
        return normalized_history

    @staticmethod
    def _build_adapter_payload(request, validated, conversation):
        payload = {
            "farm_uuid": str(conversation.farm.farm_uuid) if conversation.farm else "",
            "query": validated.get("query", ""),
            "history": ConversationAccessMixin._serialize_history_messages(validated.get("history", [])),
            "image_urls": validated.get("image_urls", []),
            "images": validated.get("images", []),
            "conversation_id": str(conversation.uuid),
            "user_id": request.user.id,
        }
        return payload

    @staticmethod
    def _attach_uploaded_files(payload, uploaded_images):
        if not uploaded_images:
            return payload

        files = []
        for uploaded_image in uploaded_images:
            files.append(
                (
                    "images",
                    (
                        uploaded_image.name,
                        uploaded_image,
                        getattr(uploaded_image, "content_type", "application/octet-stream"),
                    ),
                )
            )

        multipart_payload = dict(payload)
        multipart_payload["history"] = json.dumps(payload.get("history", []), ensure_ascii=False)
        multipart_payload["image_urls"] = json.dumps(payload.get("image_urls", []), ensure_ascii=False)
        multipart_payload["__files__"] = files
        return multipart_payload

    @staticmethod
    def _parse_json_array(value):
        if not isinstance(value, str):
            return None
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError):
            return None
        return parsed if isinstance(parsed, list) else None

    def _collect_uploaded_images(self, request):
        uploaded_images = []
        single_image = request.FILES.get("image")
        if single_image is not None:
            uploaded_images.append(single_image)
        uploaded_images.extend(request.FILES.getlist("images"))
        return uploaded_images

    def _merge_history(self, validated, conversation):
        provided_history = validated.get("history", [])
        if provided_history:
            return self._serialize_history_messages(provided_history)

        existing_messages = conversation.messages.order_by("created_at")
        return [
            {
                "role": message.role,
                "content": message.content,
                **({"sections": message.raw_response.get("sections", [])} if message.role == Message.ROLE_ASSISTANT else {}),
            }
            for message in existing_messages
            if message.content or (message.role == Message.ROLE_ASSISTANT and message.raw_response.get("sections"))
        ]

    def _prepare_chat_input(self, request):
        mutable_data = request.data.copy()

        for field_name in ("message", "content", "title", "farm_context"):
            if field_name in mutable_data:
                mutable_data.pop(field_name)

        if "history" in mutable_data:
            parsed_history = self._parse_json_array(mutable_data.get("history"))
            if parsed_history is not None:
                mutable_data["history"] = parsed_history

        if "image_urls" in mutable_data and isinstance(mutable_data.get("image_urls"), str):
            parsed_urls = self._parse_json_array(mutable_data.get("image_urls"))
            if parsed_urls is not None:
                mutable_data.setlist("image_urls", parsed_urls) if hasattr(mutable_data, "setlist") else mutable_data.__setitem__("image_urls", parsed_urls)

        if "images" in mutable_data and isinstance(mutable_data.get("images"), str):
            parsed_images = self._parse_json_array(mutable_data.get("images"))
            if parsed_images is not None:
                mutable_data.setlist("images", parsed_images) if hasattr(mutable_data, "setlist") else mutable_data.__setitem__("images", parsed_images)

        return mutable_data

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
        try:
            chat_input = self._prepare_chat_input(request)
        except ParseError:
            return Response(
                {
                    "status": "error",
                    "data": {
                        "message": "Invalid JSON body. Use valid JSON and remove extra trailing characters.",
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ChatPostSerializer(data=chat_input)
        serializer.is_valid(raise_exception=True)

        validated = serializer.validated_data
        conversation = self._get_or_create_conversation(request, validated)
        history = self._merge_history(validated, conversation)
        uploaded_images = self._collect_uploaded_images(request)

        user_message = Message.objects.create(
            conversation=conversation,
            farm=conversation.farm,
            role=Message.ROLE_USER,
            content=validated.get("query", ""),
            images=validated.get("image_urls", []) + validated.get("images", []),
            raw_response={
                "farm_uuid": self._farm_uuid_or_none(conversation.farm),
                "history": history,
            },
        )

        adapter_payload = self._build_adapter_payload(request, validated, conversation)
        adapter_payload["history"] = history
        adapter_payload = self._attach_uploaded_files(adapter_payload, uploaded_images)

        try:
            adapter_response = external_api_request(
                "ai",
                "/api/rag/chat/",
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
        except ExternalAPIRequestError as exc:
            return Response(
                {
                    "status": "error",
                    "data": {
                        "message": str(exc) or "External AI service is unavailable.",
                    },
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

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
            conversation.title = self._generate_conversation_title(validated.get("query", ""))
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
