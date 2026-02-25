"""
Farm AI Assistant API views.
Plain Django only; no DRF. No database. All responses are static mock data.
Response format: {"status": "success", "data": <payload>}. HTTP 200 only.
No processing, validation, or use of input parameters in responses.
CSRF exempt on POST so frontend can call without token.
"""

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .mock_data import CHAT_RESPONSE_DATA, CONTEXT_RESPONSE_DATA


class ContextView(View):
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

    def get(self, request):
        return JsonResponse(
            {"status": "success", "data": CONTEXT_RESPONSE_DATA},
            status=200,
        )


@method_decorator(csrf_exempt, name="dispatch")
class ChatView(View):
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

    def post(self, request):
        return JsonResponse(
            {"status": "success", "data": CHAT_RESPONSE_DATA},
            status=200,
        )
