from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from config.swagger import status_response
from .serializers import CropHealthSummarySerializer
from .services import get_crop_health_summary_data


class CropHealthSummaryView(APIView):
    @extend_schema(
        tags=["Crop Health"],
        parameters=[
            OpenApiParameter(
                name="farm_uuid",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                required=False,
                description="UUID of the farm for crop health data.",
                default="11111111-1111-1111-1111-111111111111",
            ),
        ],
        responses={200: status_response("CropHealthSummaryResponse", data=CropHealthSummarySerializer())},
    )
    def get(self, request):
        return Response(
            {"status": "success", "data": get_crop_health_summary_data()},
            status=status.HTTP_200_OK,
        )
