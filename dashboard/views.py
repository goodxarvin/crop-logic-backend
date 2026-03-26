"""
Farm Dashboard API views.
"""

from rest_framework import status
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, extend_schema_view

from config.swagger import code_response
from .mock_data import get_config, update_config
from .serializers import FarmDashboardConfigPatchSerializer, FarmDashboardConfigSerializer


@extend_schema_view(
    get=extend_schema(
        tags=["Farm Dashboard"],
        responses={200: code_response("FarmDashboardConfigGetResponse", data=FarmDashboardConfigSerializer())},
    ),
    patch=extend_schema(
        tags=["Farm Dashboard"],
        request=FarmDashboardConfigPatchSerializer,
        responses={200: code_response("FarmDashboardConfigPatchResponse", data=FarmDashboardConfigSerializer())},
    ),
)
class FarmDashboardConfigView(APIView):
    """
    Farm dashboard config endpoints.
    GET returns the current config.
    PATCH accepts partial updates and returns the full final config.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        config = get_config()
        return Response({"code": 200, "msg": "OK", "data": config}, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = FarmDashboardConfigPatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        config = update_config(serializer.validated_data)
        response_serializer = FarmDashboardConfigSerializer(config)
        return Response(
            {"code": 200, "msg": "OK", "data": response_serializer.data},
            status=status.HTTP_200_OK,
        )


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
        from external_api_adapter import request as external_api_request

        adapter_response = external_api_request("ai", "/dashboard-data/status", method="GET")
        return Response(adapter_response.data, status=adapter_response.status_code)
