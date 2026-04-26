from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from config.swagger import farm_uuid_query_param, status_response
from external_api_adapter import request as external_api_request
from farm_hub.models import FarmHub

from .serializers import CropHealthRequestSerializer, CropHealthSummarySerializer, NdviHealthCardSerializer
from .services import get_crop_health_summary_data


class CropHealthSummaryView(APIView):
    @extend_schema(
        tags=["Crop Health"],
        parameters=[
            farm_uuid_query_param(required=False, description="UUID of the farm for crop health data."),
        ],
        responses={200: status_response("CropHealthSummaryResponse", data=CropHealthSummarySerializer())},
    )
    def get(self, request):
        return Response(
            {"status": "success", "data": get_crop_health_summary_data()},
            status=status.HTTP_200_OK,
        )


class NdviHealthView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _extract_result(adapter_data):
        if not isinstance(adapter_data, dict):
            return {}

        data = adapter_data.get("data")
        if isinstance(data, dict) and isinstance(data.get("result"), dict):
            return data["result"]
        if isinstance(data, dict):
            return data

        result = adapter_data.get("result")
        if isinstance(result, dict):
            return result

        return adapter_data

    @extend_schema(
        tags=["Crop Health"],
        request=CropHealthRequestSerializer,
        responses={200: status_response("NdviHealthResponse", data=NdviHealthCardSerializer())},
    )
    def post(self, request):
        serializer = CropHealthRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            farm = FarmHub.objects.get(farm_uuid=serializer.validated_data["farm_uuid"], owner=request.user)
        except FarmHub.DoesNotExist:
            return Response({"code": 404, "msg": "Farm not found."}, status=status.HTTP_404_NOT_FOUND)

        adapter_response = external_api_request(
            "ai",
            "/api/soil-data/ndvi-health/",
            method="POST",
            payload={"farm_uuid": str(farm.farm_uuid)},
        )
        if adapter_response.status_code >= 400:
            response_data = (
                adapter_response.data
                if isinstance(adapter_response.data, dict)
                else {"message": str(adapter_response.data)}
            )
            return Response(
                {"code": adapter_response.status_code, "msg": "error", "data": response_data},
                status=adapter_response.status_code,
            )

        data = self._extract_result(adapter_response.data)
        return Response({"code": 200, "msg": "success", "data": data}, status=status.HTTP_200_OK)
