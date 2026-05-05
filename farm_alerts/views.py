import logging

from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from config.integration_contract import build_integration_meta
from config.swagger import code_response
from farm_hub.models import FarmHub

from .serializers import AlertTrackerAIResponseSerializer, FarmAlertsTrackerRequestSerializer
from .services import AlertService, build_tracker_response_from_snapshot

logger = logging.getLogger("farm_alerts")


class FarmAlertsBaseView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _get_farm(request, farm_uuid):
        if not farm_uuid:
            raise serializers.ValidationError({"farm_uuid": ["This field is required."]})
        try:
            return FarmHub.objects.get(farm_uuid=farm_uuid, owner=request.user)
        except FarmHub.DoesNotExist as exc:
            raise serializers.ValidationError({"farm_uuid": ["Farm not found."]}) from exc


class AlertTrackerView(FarmAlertsBaseView):
    @extend_schema(
        tags=["Farm Alerts"],
        request=FarmAlertsTrackerRequestSerializer,
        examples=[
            OpenApiExample(
                "Tracker Request",
                value={
                    "farm_uuid": "11111111-1111-1111-1111-111111111111",
                },
                request_only=True,
            )
        ],
        responses={200: code_response("FarmAlertsTrackerResponse", data=AlertTrackerAIResponseSerializer())},
    )
    def post(self, request):
        request_serializer = FarmAlertsTrackerRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        farm = self._get_farm(request, request_serializer.validated_data["farm_uuid"])
        logger.info(
            "tracker endpoint received request farm=%s payload=%s",
            farm.farm_uuid,
            request.data,
        )

        response_data = build_tracker_response_from_snapshot(farm=farm)
        logger.info(
            "tracker endpoint returning cached response farm=%s response=%s",
            farm.farm_uuid,
            response_data,
        )
        serializer = AlertTrackerAIResponseSerializer(instance=response_data)
        snapshot = getattr(farm, "alert_tracker_snapshot", None)
        return Response(
            {
                "code": 200,
                "msg": "success",
                "data": serializer.data,
                "meta": build_integration_meta(
                    flow_type="cached_snapshot",
                    source_type="cached_snapshot",
                    source_service="backend_farm_alerts_snapshot",
                    ownership="backend",
                    live=False,
                    cached=True,
                    snapshot_at=getattr(snapshot, "updated_at", None),
                    notes=["Returns persisted tracker snapshot, not live AI inference."],
                ),
            },
            status=status.HTTP_200_OK,
        )
