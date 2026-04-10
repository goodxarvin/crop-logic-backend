from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from farm_hub.models import FarmHub

from .mock_data import (
    ANOMALY_DETECTION_CARD,
    ARM_ALERTS_TRACKER,
    FARM_ALERTS_TIMELINE,
    RECOMMENDATIONS_LIST,
)
from .serializers import (
    AlertTimelineSerializer,
    AlertTrackerSerializer,
    AnomalyDetectionSerializer,
    CreateAlertSerializer,
    RecommendationsListSerializer,
)
from .services import AlertService


class AlertTrackerView(APIView):
    def get(self, request):
        serializer = AlertTrackerSerializer(ARM_ALERTS_TRACKER)
        return Response({"status": "success", "result": serializer.data})


class AlertTimelineView(APIView):
    def get(self, request):
        serializer = AlertTimelineSerializer(FARM_ALERTS_TIMELINE)
        return Response({"status": "success", "result": serializer.data})


class AnomalyDetectionView(APIView):
    def get(self, request):
        serializer = AnomalyDetectionSerializer(ANOMALY_DETECTION_CARD)
        return Response({"status": "success", "result": serializer.data})


class RecommendationsListView(APIView):
    def get(self, request):
        serializer = RecommendationsListSerializer(RECOMMENDATIONS_LIST)
        return Response({"status": "success", "result": serializer.data})


class CreateAlertView(APIView):
    def post(self, request):
        serializer = CreateAlertSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"status": "error", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        farm = None
        farm_uuid = data.get("farm_uuid")
        if farm_uuid:
            try:
                farm = FarmHub.objects.get(uuid=farm_uuid)
            except FarmHub.DoesNotExist:
                return Response(
                    {"status": "error", "message": "farm not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        alert = AlertService.create_alert(
            title=data["title"],
            description=data.get("description", ""),
            color=data.get("color", "info"),
            avatar_icon=data.get("avatar_icon", ""),
            avatar_color=data.get("avatar_color", ""),
            farm=farm,
        )

        return Response(
            {"status": "success", "result": {"uuid": str(alert.uuid), "title": alert.title}},
            status=status.HTTP_201_CREATED,
        )
