"""
Farm Dashboard API views.
No database connection. All responses use static mock data from mock_data.py.
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .mock_data import ALL_CARDS, CONFIG


class FarmDashboardConfigView(APIView):
    """
    Farm dashboard config endpoints: GET and PATCH.
    GET returns static config (disabled_card_ids, row_order, enable_drag_reorder).
    PATCH accepts body but returns same static config; no processing or validation.
    No database. No input values used in response.
    """
    authentication_classes = []  # No authentication
    permission_classes = []

    def get(self, request):
        return Response({"code": 200, "msg": "OK", "data": CONFIG}, status=status.HTTP_200_OK)

    def patch(self, request):
        return Response({"code": 200, "msg": "OK", "data": CONFIG}, status=status.HTTP_200_OK)


class FarmDashboardCardsView(APIView):
    """
    Farm dashboard cards endpoint: GET.
    Returns unified response with all 15 card payloads.
    No database. Static mock data only.
    """
    authentication_classes = []  # No authentication
    permission_classes = []

    def get(self, request):
        return Response({"code": 200, "msg": "OK", "data": ALL_CARDS}, status=status.HTTP_200_OK)
