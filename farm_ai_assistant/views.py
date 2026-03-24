"""
Farm AI Assistant API views.
No database. All responses are static mock data.
Response format: {"status": "success", "data": <payload>}. HTTP 200 only.
No processing, validation, or use of input parameters in responses.
"""

from django.http import HttpResponse
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema

from config.swagger import status_response
from external_api_adapter import request as external_api_request
from .mock_data import CONTEXT_RESPONSE_DATA


class ContextView(APIView):
    """
    GET endpoint for farm context (Farm AI Assistant bar).

    Purpose:
        Returns static farm context for the Farm AI Assistant UI bar:
        soilType, waterEC, selectedCrop, growthStage, lastIrrigationStatus.
        Used when loading the farm-ai-assistant page to populate the context strip.

    Input parameters:
        None. Query parameters, if sent, are not read or used.

    Response structure:
        - status: string, always "success".
        - data: object with keys soilType, waterEC, selectedCrop,
          growthStage, lastIrrigationStatus (all strings).

    No processing or validation is performed on inputs.
    """

    @extend_schema(
        tags=["Farm AI Assistant"],
        responses={200: status_response("FarmAiAssistantContextResponse", data=serializers.JSONField())},
    )
    def get(self, request):
        return Response(
            {"status": "success", "data": CONTEXT_RESPONSE_DATA},
            status=status.HTTP_200_OK,
        )


class ChatView(APIView):
    """
    POST endpoint for Farm AI Assistant chat (send message, get structured reply).

    Purpose:
        Accepts user message (and optional images, conversation_id, farm_context)
        and returns a static structured reply with sections (recommendation,
        list, warning) for rendering as cards in the chat UI. No AI or
        computation; response is fixed.

    Input parameters (body, JSON; all optional except conceptually content):
        - content: string. Location: body. User message text. Not read or used.
        - images: array of strings (URLs or base64). Location: body. Not read.
        - conversation_id: string. Location: body. Conversation id. Not used.
        - farm_context: object (soilType, waterEC, selectedCrop, growthStage,
          lastIrrigationStatus). Location: body. Not read or used.

    Response structure:
        - status: string, always "success".
        - data: object with message_id, conversation_id, content (string),
          sections (array of section objects). Each section has type, title,
          icon, and type-specific fields (content, items, frequency, amount,
          timing, expandableExplanation).

    No processing or validation is performed on inputs. Input values are
    not used in the response.
    """

    @extend_schema(
        tags=["Farm AI Assistant"],
        request=OpenApiTypes.OBJECT,
        responses={200: status_response("FarmAiAssistantChatResponse", data=serializers.JSONField())},
    )
    def post(self, request):
        adapter_response = external_api_request(
            "ai",
            "/rag/chat",
            method="POST",
            payload=request.data,
        )
        if isinstance(adapter_response.data, dict) and "body" in adapter_response.data:
            return HttpResponse(
                adapter_response.data["body"],
                status=adapter_response.status_code,
                content_type=adapter_response.data.get("content_type", "text/plain; charset=utf-8"),
            )
        return Response(adapter_response.data, status=adapter_response.status_code)
