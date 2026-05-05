"""
Farm Dashboard API views.
"""

from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view

from config.swagger import code_response
from farm_hub.models import FarmHub
from .defaults import get_default_dashboard_config
from .services import get_farm_dashboard_cards
from .models import FarmDashboardConfig
from .serializers import FarmDashboardConfigPatchSerializer, FarmDashboardConfigSerializer


class FarmAccessMixin:
    @staticmethod
    def _get_farm(request, farm_uuid):
        if not farm_uuid:
            raise serializers.ValidationError({"farm_uuid": ["This field is required."]})
        try:
            return FarmHub.objects.get(farm_uuid=farm_uuid, owner=request.user)
        except FarmHub.DoesNotExist as exc:
            raise serializers.ValidationError({"farm_uuid": ["Farm not found."]}) from exc

    @staticmethod
    def _get_or_create_dashboard_config(farm):
        default_config = get_default_dashboard_config()
        config, _created = FarmDashboardConfig.objects.get_or_create(
            farm=farm,
            defaults={
                "disabled_card_ids": default_config["disabled_card_ids"],
                "row_order": default_config["row_order"],
                "enable_drag_reorder": default_config["enable_drag_reorder"],
            },
        )
        return config

    @staticmethod
    def _serialize_config(config):
        return {
            "farm_uuid": str(config.farm.farm_uuid),
            "disabled_card_ids": config.disabled_card_ids,
            "row_order": config.row_order,
            "enable_drag_reorder": config.enable_drag_reorder,
        }


@extend_schema_view(
    get=extend_schema(
        tags=["Farm Dashboard"],
        parameters=[
            OpenApiParameter(name="farm_uuid", type=OpenApiTypes.UUID, location=OpenApiParameter.QUERY, required=True, default="11111111-1111-1111-1111-111111111111"),
        ],
        responses={200: code_response("FarmDashboardConfigGetResponse", data=FarmDashboardConfigSerializer())},
    ),
    patch=extend_schema(
        tags=["Farm Dashboard"],
        request=FarmDashboardConfigPatchSerializer,
        responses={200: code_response("FarmDashboardConfigPatchResponse", data=FarmDashboardConfigSerializer())},
    ),
)
class FarmDashboardConfigView(FarmAccessMixin, APIView):
    """
    Farm dashboard config endpoints.
    GET/PATCH are persisted in DB per farm.
    """

    permission_classes = [IsAuthenticated]
    required_feature_code = "greenhouse-dashboard"

    def get(self, request):
        farm = self._get_farm(request, request.query_params.get("farm_uuid"))
        config = self._get_or_create_dashboard_config(farm)
        return Response(
            {"code": 200, "msg": "OK", "data": self._serialize_config(config)},
            status=status.HTTP_200_OK,
        )

    def patch(self, request):
        serializer = FarmDashboardConfigPatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        farm = self._get_farm(request, serializer.validated_data["farm_uuid"])
        config = self._get_or_create_dashboard_config(farm)

        update_fields = ["updated_at"]
        if "disabled_card_ids" in serializer.validated_data:
            config.disabled_card_ids = serializer.validated_data["disabled_card_ids"]
            update_fields.append("disabled_card_ids")
        if "row_order" in serializer.validated_data:
            config.row_order = serializer.validated_data["row_order"]
            update_fields.append("row_order")
        if "enable_drag_reorder" in serializer.validated_data:
            config.enable_drag_reorder = serializer.validated_data["enable_drag_reorder"]
            update_fields.append("enable_drag_reorder")
        config.save(update_fields=update_fields)

        return Response(
            {"code": 200, "msg": "OK", "data": self._serialize_config(config)},
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    get=extend_schema(
        tags=["Farm Dashboard"],
        parameters=[
            OpenApiParameter(name="farm_uuid", type=OpenApiTypes.UUID, location=OpenApiParameter.QUERY, required=True, default="11111111-1111-1111-1111-111111111111"),
        ],
        responses={200: code_response("FarmDashboardCardsResponse", data=serializers.JSONField())},
    ),
)
class FarmDashboardCardsView(FarmAccessMixin, APIView):
    """
    Farm dashboard cards endpoint: GET.
    Requires farm_uuid and assembles local dashboard services.
    """

    permission_classes = [IsAuthenticated]
    required_feature_code = "greenhouse-dashboard"

    def get(self, request):
        farm = self._get_farm(request, request.query_params.get("farm_uuid"))
        return Response(
            {"code": 200, "msg": "OK", "data": get_farm_dashboard_cards(farm)},
            status=status.HTTP_200_OK,
        )
