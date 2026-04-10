from rest_framework import serializers, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework.permissions import IsAuthenticated

from config.swagger import code_response
from notifications.serializers import FarmNotificationSerializer

from .authentication import SensorExternalAPIKeyAuthentication
from .serializers import (
    SensorExternalRequestLogQuerySerializer,
    SensorExternalRequestLogSerializer,
    SensorExternalRequestSerializer,
)
from .services import (
    FarmDataForwardError,
    create_sensor_external_notification,
    forward_sensor_payload_to_farm_data,
    get_farm_sensor_map_for_logs,
    get_sensor_external_request_logs_for_farm,
)


class SensorExternalRequestLogPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class SensorExternalAPIView(APIView):
    authentication_classes = [SensorExternalAPIKeyAuthentication]
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Sensor External API"],
        request=SensorExternalRequestSerializer,
        parameters=[
            OpenApiParameter(
                name="X-API-Key",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=True,
                default="12345",
                description="API key for sensor external API.",
            )
        ],
        responses={
            201: code_response("SensorExternalAPIResponse", data=FarmNotificationSerializer()),
            401: code_response("SensorExternalAPIUnauthorizedResponse"),
            404: code_response("SensorExternalAPIDeviceNotFoundResponse"),
            503: code_response("SensorExternalAPIUnavailableResponse"),
        },
    )
    def post(self, request):
        serializer = SensorExternalRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            notification = create_sensor_external_notification(
                physical_device_uuid=serializer.validated_data["uuid"],
                payload=serializer.validated_data.get("payload"),
            )
            forward_sensor_payload_to_farm_data(
                physical_device_uuid=serializer.validated_data["uuid"],
                payload=serializer.validated_data.get("payload"),
            )
        except ValueError as exc:
            if "not migrated" in str(exc):
                return Response(
                    {"code": 503, "msg": "Required tables are not ready. Run migrations."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            return Response({"code": 404, "msg": "Physical device not found."}, status=status.HTTP_404_NOT_FOUND)
        except FarmDataForwardError as exc:
            return Response(
                {"code": 503, "msg": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        data = FarmNotificationSerializer(notification).data
        return Response({"code": 201, "msg": "success", "data": data}, status=status.HTTP_201_CREATED)


class SensorExternalRequestLogListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    pagination_class = SensorExternalRequestLogPagination

    @extend_schema(
        tags=["Sensor External API"],
        parameters=[
            OpenApiParameter(name="farm_uuid", type=OpenApiTypes.UUID, location=OpenApiParameter.QUERY, required=True, default="11111111-1111-1111-1111-111111111111"),
            OpenApiParameter(name="page", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter(name="page_size", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, required=False),

        ],
        responses={
            200: code_response(
                "SensorExternalRequestLogListResponse",
                data=SensorExternalRequestLogSerializer(many=True),
                extra_fields={
                    "count": serializers.IntegerField(),
                    "next": serializers.CharField(allow_null=True),
                    "previous": serializers.CharField(allow_null=True),
                },
            ),
            401: code_response("SensorExternalRequestLogListUnauthorizedResponse"),
            503: code_response("SensorExternalRequestLogListUnavailableResponse"),
        },
    )
    def get(self, request):
        serializer = SensorExternalRequestLogQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        try:
            queryset = get_sensor_external_request_logs_for_farm(
                farm_uuid=serializer.validated_data["farm_uuid"],
            )
        except ValueError:
            return Response(
                {"code": 503, "msg": "Required tables are not ready. Run migrations."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        paginator = self.pagination_class()
        paginator.page_size = serializer.validated_data["page_size"]
        page = paginator.paginate_queryset(queryset, request, view=self)
        farm_sensor_map = get_farm_sensor_map_for_logs(logs=page)
        data = SensorExternalRequestLogSerializer(
            page,
            many=True,
            context={"farm_sensor_map": farm_sensor_map},
        ).data
        return Response(
            {
                "code": 200,
                "msg": "success",
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "data": data,
            },
            status=status.HTTP_200_OK,
        )
