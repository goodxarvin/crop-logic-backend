from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from config.swagger import code_response
from farm_hub.models import FarmHub

from .serializers import Sensor7In1SummarySerializer
from .services import get_sensor_7_in_1_summary_data


class Sensor7In1SummaryView(APIView):
    permission_classes = [IsAuthenticated]
    required_feature_code = "sensor-7-in-1"

    @staticmethod
    def _get_farm(request):
        farm_uuid = request.query_params.get("farm_uuid")
        if not farm_uuid:
            raise serializers.ValidationError({"farm_uuid": ["This field is required."]})
        try:
            return FarmHub.objects.get(farm_uuid=farm_uuid, owner=request.user)
        except FarmHub.DoesNotExist as exc:
            raise serializers.ValidationError({"farm_uuid": ["Farm not found."]}) from exc

    @extend_schema(
        tags=["Sensor 7 in 1"],
        parameters=[
            OpenApiParameter(
                name="farm_uuid",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                required=True,
                default="11111111-1111-1111-1111-111111111111",
            )
        ],
        responses={200: code_response("Sensor7In1SummaryResponse", data=Sensor7In1SummarySerializer())},
    )
    def get(self, request):
        farm = self._get_farm(request)
        return Response(
            {"code": 200, "msg": "OK", "data": get_sensor_7_in_1_summary_data(farm)},
            status=status.HTTP_200_OK,
        )

