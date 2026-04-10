from rest_framework.response import Response
from rest_framework.views import APIView

from .mock_data import ECONOMIC_OVERVIEW
from .serializers import EconomicOverviewSerializer


class EconomicOverviewView(APIView):
    def get(self, request):
        serializer = EconomicOverviewSerializer(ECONOMIC_OVERVIEW)
        return Response({"status": "success", "result": serializer.data})
