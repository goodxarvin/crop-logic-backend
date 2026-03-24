"""
Farm Dashboard API views.
No database connection. All responses use static mock data from mock_data.py.
"""

from rest_framework import status
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view

from config.swagger import code_response
from external_api_adapter import request as external_api_request
from .mock_data import CONFIG


@extend_schema_view(
    get=extend_schema(
        tags=["Farm Dashboard"],
        responses={200: code_response("FarmDashboardConfigGetResponse", data=serializers.JSONField())},
    ),
    patch=extend_schema(
        tags=["Farm Dashboard"],
        request=OpenApiTypes.OBJECT,
        responses={200: code_response("FarmDashboardConfigPatchResponse", data=serializers.JSONField())},
    ),
)
class FarmDashboardConfigView(APIView):
    """
    Farm dashboard config endpoints: GET and PATCH.
    GET returns static config (disabled_card_ids, row_order, enable_drag_reorder).
    PATCH accepts body but returns same static config; no processing or validation.
    No database. No input values used in response.
    """
    def get(self, request):
        return Response({"code": 200, "msg": "OK", "data": CONFIG}, status=status.HTTP_200_OK)

    def patch(self, request):
        return Response({"code": 200, "msg": "OK", "data": CONFIG}, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        tags=["Farm Dashboard"],
        responses={200: code_response("FarmDashboardCardsResponse", data=serializers.JSONField())},
    ),
)
class FarmDashboardCardsView(APIView):
    """
    Farm dashboard cards endpoint: GET.
    Returns unified response with all 15 card payloads.
    No database. Static mock data only.
    """
    def get(self, request):
        adapter_response = external_api_request("ai", "/dashboard-data/status", method="GET")
        return Response(adapter_response.data, status=adapter_response.status_code)
