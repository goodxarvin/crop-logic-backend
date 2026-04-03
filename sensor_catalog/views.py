from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from config.swagger import code_response
from .models import SensorCatalog
from .serializers import SensorCatalogSerializer


class SensorCatalogListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Sensor Catalog"],
        responses={200: code_response("SensorCatalogListResponse", data=SensorCatalogSerializer(many=True))},
    )
    def get(self, request):
        sensors = SensorCatalog.objects.order_by("name")
        data = SensorCatalogSerializer(sensors, many=True).data
        return Response({"code": 200, "msg": "success", "data": data}, status=status.HTTP_200_OK)
