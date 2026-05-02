from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import NotFound
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from farm_hub.models import FarmHub

from .enums import FARMER_TAG_ITEMS
from .models import FarmerCalendarEvent
from .serializers import (
    FarmerCalendarEventResponseSerializer,
    FarmerCalendarEventWriteSerializer,
    FarmerCalendarListQuerySerializer,
    FarmerCalendarTagIdSerializer,
)


class FarmerCalendarBaseView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def error_response(message, details=None, code="EVENT_VALIDATION_ERROR", status_code=status.HTTP_400_BAD_REQUEST):
        payload = {
            "code": code,
            "message": message,
        }
        if details is not None:
            payload["details"] = details
        return Response(payload, status=status_code)

    def handle_exception(self, exc):
        if isinstance(exc, serializers.ValidationError):
            details = exc.detail
            message = "Invalid event payload"
            if isinstance(details, dict):
                first_value = next(iter(details.values()), None)
                if isinstance(first_value, list) and first_value:
                    message = str(first_value[0])
                elif first_value:
                    message = str(first_value)
            elif isinstance(details, list) and details:
                message = str(details[0])
            return self.error_response(message=message, details=details)
        if isinstance(exc, NotFound):
            return self.error_response(
                message=str(exc.detail),
                code="EVENT_NOT_FOUND",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return super().handle_exception(exc)

    def _get_user_farms(self, request):
        return FarmHub.objects.filter(owner=request.user).order_by("id")

    def _resolve_farm(self, request, farm_uuid=None, required=False):
        farms = self._get_user_farms(request)
        if farm_uuid:
            try:
                return farms.get(farm_uuid=farm_uuid)
            except FarmHub.DoesNotExist as exc:
                raise serializers.ValidationError({"farm_uuid": ["Farm not found."]}) from exc

        if required:
            farm_count = farms.count()
            if farm_count == 1:
                return farms.first()
            if farm_count == 0:
                raise serializers.ValidationError({"farm_uuid": ["No farm found for this user."]})
            raise serializers.ValidationError({"farm_uuid": ["farm_uuid is required when multiple farms exist."]})
        return None

    def _get_event(self, request, event_id):
        queryset = FarmerCalendarEvent.objects.select_related("farm").prefetch_related("tags")
        try:
            return queryset.get(uuid=event_id, farm__owner=request.user)
        except FarmerCalendarEvent.DoesNotExist as exc:
            raise NotFound("Event not found.") from exc


class EventListCreateView(FarmerCalendarBaseView):
    @extend_schema(
        tags=["Farmer Calendar"],
        parameters=[
            OpenApiParameter(name="start", type=OpenApiTypes.DATETIME, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter(name="end", type=OpenApiTypes.DATETIME, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter(name="farm_uuid", type=OpenApiTypes.UUID, location=OpenApiParameter.QUERY, required=False),
        ],
    )
    def get(self, request):
        query_serializer = FarmerCalendarListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        queryset = FarmerCalendarEvent.objects.filter(farm__owner=request.user).prefetch_related("tags")
        farm = self._resolve_farm(request, query_serializer.validated_data.get("farm_uuid"), required=False)
        if farm is not None:
            queryset = queryset.filter(farm=farm)

        start = query_serializer.validated_data.get("start")
        end = query_serializer.validated_data.get("end")
        if start:
            queryset = queryset.filter(end__gte=start)
        if end:
            queryset = queryset.filter(start__lte=end)

        events = queryset.order_by("start", "created_at")
        data = FarmerCalendarEventResponseSerializer(events, many=True).data
        return Response({"events": data, "meta": {"total": len(data)}}, status=status.HTTP_200_OK)

    @extend_schema(tags=["Farmer Calendar"])
    def post(self, request):
        serializer = FarmerCalendarEventWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        farm = self._resolve_farm(request, serializer.validated_data.get("farm_uuid"), required=True)
        event = serializer.save(farm=farm)
        data = FarmerCalendarEventResponseSerializer(event).data
        return Response({"event": data}, status=status.HTTP_201_CREATED)


class EventTagListView(FarmerCalendarBaseView):
    @extend_schema(
        tags=["Farmer Calendar"],
        parameters=[
            OpenApiParameter(name="farm_uuid", type=OpenApiTypes.UUID, location=OpenApiParameter.QUERY, required=False),
        ],
    )
    def get(self, request):
        self._resolve_farm(request, request.query_params.get("farm_uuid"), required=False)
        data = FarmerCalendarTagIdSerializer(FARMER_TAG_ITEMS, many=True).data
        return Response({"tags": data, "meta": {"total": len(data)}}, status=status.HTTP_200_OK)


class EventDetailView(FarmerCalendarBaseView):
    @extend_schema(tags=["Farmer Calendar"])
    def get(self, request, event_id):
        event = self._get_event(request, event_id)
        data = FarmerCalendarEventResponseSerializer(event).data
        return Response({"event": data}, status=status.HTTP_200_OK)

    @extend_schema(tags=["Farmer Calendar"])
    def put(self, request, event_id):
        event = self._get_event(request, event_id)
        serializer = FarmerCalendarEventWriteSerializer(event, data=request.data)
        serializer.is_valid(raise_exception=True)

        requested_farm_uuid = serializer.validated_data.get("farm_uuid")
        if requested_farm_uuid and str(event.farm.farm_uuid) != str(requested_farm_uuid):
            return self.error_response(
                message="farm_uuid cannot change an existing event",
                details={"farm_uuid": ["farm_uuid cannot change an existing event"]},
            )

        event = serializer.save()
        data = FarmerCalendarEventResponseSerializer(event).data
        return Response({"event": data}, status=status.HTTP_200_OK)

    @extend_schema(tags=["Farmer Calendar"])
    def delete(self, request, event_id):
        event = self._get_event(request, event_id)
        event.delete()
        return Response({"success": True}, status=status.HTTP_200_OK)
