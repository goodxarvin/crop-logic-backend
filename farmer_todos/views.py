from datetime import date

from django.db.models import Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from farm_hub.models import FarmHub
from farmer_calendar.enums import FARMER_TAG_ITEMS
from farmer_calendar.models import FarmerCalendarZone

from .models import FarmerTodoTask
from .serializers import (
    FarmerTodoListQuerySerializer,
    FarmerTodoTagSerializer,
    FarmerTodoTaskResponseSerializer,
    FarmerTodoTaskWriteSerializer,
    FarmerTodoZoneSerializer,
)


class FarmerTodoBaseView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def error_response(message, details=None, code="TASK_VALIDATION_ERROR", status_code=status.HTTP_400_BAD_REQUEST):
        payload = {"code": code, "message": message}
        if details is not None:
            payload["details"] = details
        return Response(payload, status=status_code)

    def handle_exception(self, exc):
        if isinstance(exc, serializers.ValidationError):
            details = exc.detail
            message = "Invalid farmer todo payload"
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
                code="TASK_NOT_FOUND",
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

    def _get_task(self, request, task_id):
        queryset = FarmerTodoTask.objects.select_related("farm", "zone").prefetch_related("tags")
        try:
            return queryset.get(uuid=task_id, farm__owner=request.user)
        except FarmerTodoTask.DoesNotExist as exc:
            raise NotFound("Task not found.") from exc


class FarmerTodoListCreateView(FarmerTodoBaseView):
    @extend_schema(
        tags=["Farmer Todos"],
        parameters=[
            OpenApiParameter(name="status", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter(name="priority", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter(name="date", type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter(name="from", type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter(name="to", type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter(name="zone", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter(name="search", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter(name="farm_uuid", type=OpenApiTypes.UUID, location=OpenApiParameter.QUERY, required=False),
        ],
    )
    def get(self, request):
        query_data = request.query_params.copy()
        if "from" in query_data and "from_date" not in query_data:
            query_data["from_date"] = query_data["from"]
        query_serializer = FarmerTodoListQuerySerializer(data=query_data)
        query_serializer.is_valid(raise_exception=True)
        filters = query_serializer.validated_data

        queryset = FarmerTodoTask.objects.filter(farm__owner=request.user).select_related("zone").prefetch_related("tags")
        farm = self._resolve_farm(request, filters.get("farm_uuid"), required=False)
        if farm is not None:
            queryset = queryset.filter(farm=farm)
        if filters.get("status"):
            queryset = queryset.filter(status=filters["status"])
        if filters.get("priority"):
            queryset = queryset.filter(priority=filters["priority"])
        if filters.get("date"):
            queryset = queryset.filter(scheduled_date=filters["date"])
        if filters.get("from"):
            queryset = queryset.filter(scheduled_date__gte=filters["from"])
        if filters.get("to"):
            queryset = queryset.filter(scheduled_date__lte=filters["to"])
        if filters.get("zone"):
            queryset = queryset.filter(zone__value=filters["zone"].strip())
        if filters.get("search"):
            search_value = filters["search"].strip()
            queryset = queryset.filter(Q(title__icontains=search_value) | Q(description__icontains=search_value))

        tasks = queryset.order_by("scheduled_date", "time", "created_at")
        data = FarmerTodoTaskResponseSerializer(tasks, many=True).data
        return Response({"tasks": data, "meta": {"total": len(data)}}, status=status.HTTP_200_OK)

    @extend_schema(tags=["Farmer Todos"])
    def post(self, request):
        serializer = FarmerTodoTaskWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        farm = self._resolve_farm(request, serializer.validated_data.get("farm_uuid"), required=True)
        task = serializer.save(farm=farm)
        data = FarmerTodoTaskResponseSerializer(task).data
        return Response({"task": data}, status=status.HTTP_201_CREATED)


class FarmerTodoDetailView(FarmerTodoBaseView):
    @extend_schema(tags=["Farmer Todos"])
    def put(self, request, task_id):
        task = self._get_task(request, task_id)
        serializer = FarmerTodoTaskWriteSerializer(task, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        requested_farm_uuid = serializer.validated_data.get("farm_uuid")
        if requested_farm_uuid and str(task.farm.farm_uuid) != str(requested_farm_uuid):
            return self.error_response(
                message="farm_uuid cannot change an existing task",
                details={"farm_uuid": ["farm_uuid cannot change an existing task"]},
            )

        task = serializer.save()
        data = FarmerTodoTaskResponseSerializer(task).data
        return Response({"task": data}, status=status.HTTP_200_OK)

    @extend_schema(tags=["Farmer Todos"])
    def delete(self, request, task_id):
        task = self._get_task(request, task_id)
        task.delete()
        return Response({"success": True}, status=status.HTTP_200_OK)

    @extend_schema(tags=["Farmer Todos"])
    def get(self, request, task_id):
        task = self._get_task(request, task_id)
        data = FarmerTodoTaskResponseSerializer(task).data
        return Response({"task": data}, status=status.HTTP_200_OK)


class FarmerTodoZonesView(FarmerTodoBaseView):
    @extend_schema(
        tags=["Farmer Todos"],
        parameters=[
            OpenApiParameter(name="farm_uuid", type=OpenApiTypes.UUID, location=OpenApiParameter.QUERY, required=False),
        ],
    )
    def get(self, request):
        farm = self._resolve_farm(request, request.query_params.get("farm_uuid"), required=False)
        queryset = FarmerCalendarZone.objects.filter(farm__owner=request.user, is_active=True)
        if farm is not None:
            queryset = queryset.filter(farm=farm)
        if farm is None:
            unique_zones = {}
            for zone in queryset.order_by("label", "created_at"):
                unique_zones.setdefault(zone.value, zone)
            zones = list(unique_zones.values())
        else:
            zones = queryset.order_by("label")
        data = FarmerTodoZoneSerializer(zones, many=True).data
        return Response({"zones": data, "meta": {"total": len(data)}}, status=status.HTTP_200_OK)


class FarmerTodoTagsView(FarmerTodoBaseView):
    @extend_schema(
        tags=["Farmer Todos"],
        parameters=[
            OpenApiParameter(name="farm_uuid", type=OpenApiTypes.UUID, location=OpenApiParameter.QUERY, required=False),
        ],
    )
    def get(self, request):
        self._resolve_farm(request, request.query_params.get("farm_uuid"), required=False)
        data = FarmerTodoTagSerializer(FARMER_TAG_ITEMS, many=True).data
        return Response({"tags": data, "meta": {"total": len(data)}}, status=status.HTTP_200_OK)


class FarmerTodoSummaryView(FarmerTodoBaseView):
    @extend_schema(
        tags=["Farmer Todos"],
        parameters=[
            OpenApiParameter(name="farm_uuid", type=OpenApiTypes.UUID, location=OpenApiParameter.QUERY, required=False),
        ],
    )
    def get(self, request):
        farm = self._resolve_farm(request, request.query_params.get("farm_uuid"), required=False)
        queryset = FarmerTodoTask.objects.filter(farm__owner=request.user).select_related("zone").prefetch_related("tags")
        if farm is not None:
            queryset = queryset.filter(farm=farm)

        today = date.today()
        total_count = queryset.count()
        today_count = queryset.filter(scheduled_date=today).count()
        completed_count = queryset.filter(status=FarmerTodoTask.STATUS_DONE).count()
        urgent_count = queryset.filter(priority=FarmerTodoTask.PRIORITY_HIGH, status=FarmerTodoTask.STATUS_OPEN).count()
        next_task = queryset.filter(
            status=FarmerTodoTask.STATUS_OPEN,
        ).filter(
            Q(scheduled_date__gt=today) | Q(scheduled_date=today)
        ).order_by("scheduled_date", "time", "created_at").first()

        progress_value = int((completed_count / total_count) * 100) if total_count else 0
        next_task_data = FarmerTodoTaskResponseSerializer(next_task).data if next_task else None
        return Response(
            {
                "todayTasksCount": today_count,
                "completedCount": completed_count,
                "urgentCount": urgent_count,
                "progressValue": progress_value,
                "nextTask": next_task_data,
            },
            status=status.HTTP_200_OK,
        )
