from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from config.integration_contract import build_integration_meta
from config.swagger import code_response, farm_uuid_query_param
from farm_hub.models import FarmHub, Product
from .serializers import PlantNameSerializer, PlantSerializer
from .services import PlantSyncError, ensure_plant_defaults, push_plants_to_ai


class PlantBaseView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _attempt_ai_catalog_sync():
        try:
            push_plants_to_ai()
        except PlantSyncError:
            return False, "failed"
        return True, "synced"

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
        products = ensure_plant_defaults(Product.objects.order_by("name"))
        sync_attempted = True
        sync_status = "synced"
        try:
            push_plants_to_ai(products)
        except PlantSyncError as exc:
            sync_status = "failed"
            if not products:
                return Response({"code": 503, "msg": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        data = PlantSerializer(products, many=True).data
        return Response(
            {
                "code": 200,
                "msg": "success",
                "data": data,
                "meta": build_integration_meta(
                    flow_type="backend_owned_data_with_ai_enrichment",
                    source_type="db",
                    source_service="backend_plants",
                    ownership="backend",
                    live=False,
                    cached=False,
                    sync_attempted=sync_attempted,
                    sync_status=sync_status,
                    notes=["Backend plant catalog is canonical; AI receives sync snapshots only."],
                ),
            },
            status=status.HTTP_200_OK,
        )


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
        sync_attempted, sync_status = self._attempt_ai_catalog_sync()
        products = ensure_plant_defaults(Product.objects.order_by("name"))
        data = PlantNameSerializer(products, many=True).data
        return Response(
            {
                "code": 200,
                "msg": "success",
                "data": data,
                "meta": build_integration_meta(
                    flow_type="backend_owned_data",
                    source_type="db",
                    source_service="backend_plants",
                    ownership="backend",
                    live=False,
                    cached=False,
                    sync_attempted=sync_attempted,
                    sync_status=sync_status,
                ),
            },
            status=status.HTTP_200_OK,
        )


class SelectedPlantListView(PlantBaseView):
    @extend_schema(
        tags=["Plants"],
        parameters=[farm_uuid_query_param(required=True, description="UUID of the farm to read selected plants from.")],
        responses={200: code_response("SelectedPlantListResponse", data=PlantNameSerializer(many=True))},
    )
    def get(self, request):
        sync_attempted, sync_status = self._attempt_ai_catalog_sync()
        farm = self._get_farm(request, request.query_params.get("farm_uuid"))
        ensure_plant_defaults(farm.products.all())
        products = farm.products.order_by("name")
        data = PlantNameSerializer(products, many=True).data
        return Response(
            {
                "code": 200,
                "msg": "success",
                "data": data,
                "meta": build_integration_meta(
                    flow_type="backend_owned_data",
                    source_type="db",
                    source_service="backend_plants",
                    ownership="backend",
                    live=False,
                    cached=False,
                    sync_attempted=sync_attempted,
                    sync_status=sync_status,
                ),
            },
            status=status.HTTP_200_OK,
        )
