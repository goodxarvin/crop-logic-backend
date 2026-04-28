from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from config.swagger import code_response, farm_uuid_query_param
from farm_hub.models import FarmHub, Product
from .serializers import PlantNameSerializer, PlantSerializer
from .services import PlantSyncError, ensure_plant_defaults, sync_plants_from_ai


class PlantBaseView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _sync_plants_if_possible():
        try:
            sync_plants_from_ai()
        except PlantSyncError:
            return False
        return True

    @staticmethod
    def _get_farm(request, farm_uuid):
        if not farm_uuid:
            raise serializers.ValidationError({"farm_uuid": ["This field is required."]})
        try:
            return FarmHub.objects.prefetch_related("products").get(farm_uuid=farm_uuid, owner=request.user)
        except FarmHub.DoesNotExist as exc:
            raise serializers.ValidationError({"farm_uuid": ["Farm not found."]}) from exc


class PlantListView(PlantBaseView):
    @extend_schema(
        tags=["Plants"],
        responses={200: code_response("PlantListResponse", data=PlantSerializer(many=True))},
    )
    def get(self, request):
        try:
            sync_plants_from_ai()
        except PlantSyncError as exc:
            if not Product.objects.exists():
                return Response({"code": 503, "msg": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        products = ensure_plant_defaults(Product.objects.order_by("name"))
        data = PlantSerializer(products, many=True).data
        return Response({"code": 200, "msg": "success", "data": data}, status=status.HTTP_200_OK)


class PlantDetailView(PlantBaseView):
    @extend_schema(
        tags=["Plants"],
        parameters=[
            OpenApiParameter(name="plant_id", type=OpenApiTypes.INT, location=OpenApiParameter.PATH),
        ],
        responses={200: code_response("PlantDetailResponse", data=PlantSerializer())},
    )
    def get(self, request, plant_id):
        try:
            product = Product.objects.get(id=plant_id)
        except Product.DoesNotExist:
            return Response({"code": 404, "msg": "Plant not found."}, status=status.HTTP_404_NOT_FOUND)

        ensure_plant_defaults([product])
        product.refresh_from_db()
        data = PlantSerializer(product).data
        return Response({"code": 200, "msg": "success", "data": data}, status=status.HTTP_200_OK)


class PlantNameListView(PlantBaseView):
    @extend_schema(
        tags=["Plants"],
        responses={200: code_response("PlantNameListResponse", data=PlantNameSerializer(many=True))},
    )
    def get(self, request):
        self._sync_plants_if_possible()
        products = ensure_plant_defaults(Product.objects.order_by("name"))
        data = PlantNameSerializer(products, many=True).data
        return Response({"code": 200, "msg": "success", "data": data}, status=status.HTTP_200_OK)


class SelectedPlantListView(PlantBaseView):
    @extend_schema(
        tags=["Plants"],
        parameters=[farm_uuid_query_param(required=True, description="UUID of the farm to read selected plants from.")],
        responses={200: code_response("SelectedPlantListResponse", data=PlantNameSerializer(many=True))},
    )
    def get(self, request):
        self._sync_plants_if_possible()
        farm = self._get_farm(request, request.query_params.get("farm_uuid"))
        ensure_plant_defaults(farm.products.all())
        products = farm.products.order_by("name")
        data = PlantNameSerializer(products, many=True).data
        return Response({"code": 200, "msg": "success", "data": data}, status=status.HTTP_200_OK)
