from rest_framework import serializers, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiTypes, extend_schema

from config.swagger import code_response, farm_uuid_query_param
from farm_hub.models import FarmHub
from notifications.serializers import FarmNotificationSerializer
from soil.serializers import SoilComparisonChartSerializer, SoilRadarChartSerializer

from .authentication import SensorExternalAPIKeyAuthentication
from .sensor_serializers import DeviceSummarySerializer, Sensor7In1SummarySerializer, SensorComparisonChartQuerySerializer, SensorComparisonChartResponseSerializer, SensorRadarChartQuerySerializer, SensorRadarChartResponseSerializer, SensorValuesListQuerySerializer, SensorValuesListResponseSerializer
from .serializers import DeviceCatalogSerializer, DeviceCodeQuerySerializer, DeviceCommandRequestSerializer, DeviceCommandResponseSerializer, DeviceDetailSerializer, DeviceLatestPayloadSerializer, DeviceRangeQuerySerializer, SensorExternalRequestLogQuerySerializer, SensorExternalRequestLogSerializer, SensorExternalRequestSerializer
from .services import DeviceDataUnavailableError, FarmDataForwardError, build_device_comparison_chart, build_device_latest_payload, build_device_radar_chart, build_device_summary, build_device_values_list, create_sensor_external_notification, execute_device_command, forward_sensor_payload_to_farm_data, get_farm_device_by_physical_uuid, get_farm_device_map_for_logs, get_primary_soil_sensor, get_sensor_7_in_1_comparison_chart_data, get_sensor_7_in_1_radar_chart_data, get_sensor_7_in_1_summary_data, get_sensor_comparison_chart_data, get_sensor_external_request_logs_for_farm, get_sensor_radar_chart_data, get_sensor_values_list_data, validate_output_device_catalog


class DeviceCatalogListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["Sensor Catalog"], responses={200: code_response("DeviceCatalogListResponse", data=DeviceCatalogSerializer(many=True))})
    def get(self, request):
        from .models import DeviceCatalog
        return Response({"code": 200, "msg": "success", "data": DeviceCatalogSerializer(DeviceCatalog.objects.order_by("code"), many=True).data}, status=status.HTTP_200_OK)


class DeviceBaseView(APIView):
    permission_classes = [IsAuthenticated]

    def get_farm_device(self, request, physical_device_uuid):
        farm_device = get_farm_device_by_physical_uuid(physical_device_uuid=physical_device_uuid, owner=request.user)
        if farm_device is None:
            raise serializers.ValidationError({"physical_device_uuid": ["Device not found."]})
        return farm_device

    def get_device_code(self, request):
        serializer = DeviceCodeQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data["device_code"]


class DeviceDetailView(DeviceBaseView):
    @extend_schema(tags=["Device Hub"], parameters=[OpenApiParameter(name="device_code", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=True)], responses={200: code_response("DeviceDetailResponse", data=DeviceDetailSerializer())})
    def get(self, request, physical_device_uuid):
        farm_device = self.get_farm_device(request, physical_device_uuid)
        device_code = self.get_device_code(request)
        validate_output_device_catalog(farm_device=farm_device, device_code=device_code)
        latest_payload = build_device_latest_payload(farm_device, device_code=device_code)
        serializer = DeviceDetailSerializer(farm_device, context={"latest_log": type("LatestLog", (), {"created_at": latest_payload["created_at"]})() if latest_payload["created_at"] else None})
        return Response({"code": 200, "msg": "success", "data": serializer.data}, status=status.HTTP_200_OK)


class DeviceLatestPayloadView(DeviceBaseView):
    @extend_schema(tags=["Device Hub"], parameters=[OpenApiParameter(name="device_code", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=True)], responses={200: code_response("DeviceLatestPayloadResponse", data=DeviceLatestPayloadSerializer())})
    def get(self, request, physical_device_uuid):
        farm_device = self.get_farm_device(request, physical_device_uuid)
        device_code = self.get_device_code(request)
        try:
            data = build_device_latest_payload(farm_device, device_code=device_code)
        except ValueError as exc:
            raise serializers.ValidationError({"device_code": [str(exc)]}) from exc
        return Response({"code": 200, "msg": "success", "data": data}, status=status.HTTP_200_OK)


class DeviceSummaryView(DeviceBaseView):
    @extend_schema(tags=["Device Hub"], parameters=[OpenApiParameter(name="device_code", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=True)], responses={200: code_response("DeviceSummaryResponse", data=DeviceSummarySerializer())})
    def get(self, request, physical_device_uuid):
        farm_device = self.get_farm_device(request, physical_device_uuid)
        device_code = self.get_device_code(request)
        try:
            data = build_device_summary(farm_device, device_code=device_code)
        except ValueError as exc:
            raise serializers.ValidationError({"device_code": [str(exc)]}) from exc
        return Response({"code": 200, "msg": "success", "data": data}, status=status.HTTP_200_OK)


class DeviceComparisonChartView(DeviceBaseView):
    @extend_schema(tags=["Device Hub"], parameters=[OpenApiParameter(name="device_code", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=True), OpenApiParameter(name="range", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False, description="Chart range, supported values: 7d, 30d. Defaults to 7d.")], responses={200: SensorComparisonChartResponseSerializer})
    def get(self, request, physical_device_uuid):
        serializer = DeviceRangeQuerySerializer(data={"device_code": request.query_params.get("device_code"), "range": request.query_params.get("range", "7d")})
        serializer.is_valid(raise_exception=True)
        farm_device = self.get_farm_device(request, physical_device_uuid)
        try:
            data = build_device_comparison_chart(farm_device, serializer.validated_data["range"], device_code=serializer.validated_data["device_code"])
        except ValueError as exc:
            raise serializers.ValidationError({"device_code": [str(exc)]}) from exc
        return Response(data, status=status.HTTP_200_OK)


class DeviceValuesListView(DeviceBaseView):
    @extend_schema(tags=["Device Hub"], parameters=[OpenApiParameter(name="device_code", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=True), OpenApiParameter(name="range", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False, description="Values list range, supported values: 1h, 24h, 7d. Defaults to 7d.")], responses={200: SensorValuesListResponseSerializer})
    def get(self, request, physical_device_uuid):
        serializer = DeviceRangeQuerySerializer(data={"device_code": request.query_params.get("device_code"), "range": request.query_params.get("range", "7d")})
        serializer.is_valid(raise_exception=True)
        farm_device = self.get_farm_device(request, physical_device_uuid)
        try:
            data = build_device_values_list(farm_device, serializer.validated_data["range"], device_code=serializer.validated_data["device_code"])
        except ValueError as exc:
            raise serializers.ValidationError({"device_code": [str(exc)]}) from exc
        return Response(data, status=status.HTTP_200_OK)


class DeviceRadarChartView(DeviceBaseView):
    @extend_schema(tags=["Device Hub"], parameters=[OpenApiParameter(name="device_code", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=True), OpenApiParameter(name="range", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False, description="Radar chart range, supported values: today, 7d, 30d. Defaults to 7d.")], responses={200: SensorRadarChartResponseSerializer})
    def get(self, request, physical_device_uuid):
        serializer = DeviceRangeQuerySerializer(data={"device_code": request.query_params.get("device_code"), "range": request.query_params.get("range", "7d")})
        serializer.is_valid(raise_exception=True)
        farm_device = self.get_farm_device(request, physical_device_uuid)
        try:
            data = build_device_radar_chart(farm_device, serializer.validated_data["range"], device_code=serializer.validated_data["device_code"])
        except ValueError as exc:
            raise serializers.ValidationError({"device_code": [str(exc)]}) from exc
        return Response(data, status=status.HTTP_200_OK)


class SensorExternalRequestLogPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class DeviceLogListView(DeviceBaseView):
    pagination_class = SensorExternalRequestLogPagination

    @extend_schema(tags=["Device Hub"], parameters=[OpenApiParameter(name="device_code", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=True), OpenApiParameter(name="page", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, required=True), OpenApiParameter(name="page_size", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, required=True)], responses={200: code_response("DeviceLogListResponse", data=SensorExternalRequestLogSerializer(many=True), extra_fields={"count": serializers.IntegerField(), "next": serializers.CharField(allow_null=True), "previous": serializers.CharField(allow_null=True)})})
    def get(self, request, physical_device_uuid):
        page = request.query_params.get("page", 1)
        page_size = request.query_params.get("page_size", 20)
        device_code = request.query_params.get("device_code")
        serializer = SensorExternalRequestLogQuerySerializer(
            data={
                "farm_uuid": "11111111-1111-1111-1111-111111111111",
                "page": page,
                "page_size": page_size,
                "physical_device_uuid": physical_device_uuid,
            }
        )
        serializer.is_valid(raise_exception=True)
        farm_device = self.get_farm_device(request, physical_device_uuid)
        try:
            device_catalog = validate_output_device_catalog(farm_device=farm_device, device_code=device_code)
        except ValueError as exc:
            raise serializers.ValidationError({"device_code": [str(exc)]}) from exc
        queryset = get_sensor_external_request_logs_for_farm(
            farm_uuid=farm_device.farm.farm_uuid,
            physical_device_uuid=farm_device.physical_device_uuid,
        )
        queryset = queryset.filter(sensor_catalog_uuid=device_catalog.uuid)
        paginator = self.pagination_class()
        paginator.page_size = serializer.validated_data["page_size"]
        page_obj = paginator.paginate_queryset(queryset, request, view=self)
        farm_device_map = get_farm_device_map_for_logs(logs=page_obj)
        data = SensorExternalRequestLogSerializer(page_obj, many=True, context={"farm_device_map": farm_device_map}).data
        return Response({"code": 200, "msg": "success", "count": paginator.page.paginator.count, "next": paginator.get_next_link(), "previous": paginator.get_previous_link(), "data": data}, status=status.HTTP_200_OK)


class DeviceCommandView(DeviceBaseView):
    @extend_schema(tags=["Device Hub"], request=DeviceCommandRequestSerializer, responses={200: code_response("DeviceCommandResponse", data=DeviceCommandResponseSerializer())})
    def post(self, request, physical_device_uuid):
        serializer = DeviceCommandRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        farm_device = self.get_farm_device(request, physical_device_uuid)
        try:
            device_catalog = farm_device.get_device_catalog_by_code(serializer.validated_data["device_code"])
            if device_catalog is None:
                raise ValueError("Device code is not attached to this farm device.")
            result = execute_device_command(
                farm_device=farm_device,
                device_code=serializer.validated_data["device_code"],
                command=serializer.validated_data["command"],
                payload=serializer.validated_data.get("payload"),
            )
        except ValueError as exc:
            raise serializers.ValidationError({"device_code": [str(exc)]}) from exc
        return Response({"code": 200, "msg": "command accepted", "data": result}, status=status.HTTP_200_OK)


class Sensor7In1SummaryView(APIView):
    permission_classes = [IsAuthenticated]
    required_feature_code = "sensor-7-in-1"

    @staticmethod
    def _get_farm(request):
        farm_uuid = request.query_params.get("farm_uuid")
        if not farm_uuid:
            raise serializers.ValidationError({"farm_uuid": ["This field is required."]})
        try:
            return FarmHub.objects.get(farm_uuid=farm_uuid, owner=request.user)
        except FarmHub.DoesNotExist as exc:
            raise serializers.ValidationError({"farm_uuid": ["Farm not found."]}) from exc

    @staticmethod
    def _get_primary_sensor(*, farm):
        sensor = get_primary_soil_sensor(farm=farm)
        if sensor is None:
            raise serializers.ValidationError({"farm_uuid": ["No sensor found for this farm."]})
        return sensor

    @extend_schema(tags=["Sensor 7 in 1"], parameters=[farm_uuid_query_param(required=True, description="UUID of the farm for sensor 7 in 1 summary.")], responses={200: code_response("Sensor7In1SummaryResponse", data=Sensor7In1SummarySerializer())})
    def get(self, request):
        farm = self._get_farm(request)
        try:
            data = get_sensor_7_in_1_summary_data(farm)
        except DeviceDataUnavailableError as exc:
            raise serializers.ValidationError({"farm_uuid": [str(exc)]}) from exc
        return Response({"code": 200, "msg": "OK", "data": data}, status=status.HTTP_200_OK)


class Sensor7In1RadarChartView(Sensor7In1SummaryView):
    @extend_schema(tags=["Sensor 7 in 1"], parameters=[farm_uuid_query_param(required=True, description="UUID of the farm for sensor 7 in 1 radar chart.")], responses={200: code_response("Sensor7In1RadarChartResponse", data=SoilRadarChartSerializer())})
    def get(self, request):
        farm = self._get_farm(request)
        try:
            data = get_sensor_7_in_1_radar_chart_data(farm)
        except DeviceDataUnavailableError as exc:
            raise serializers.ValidationError({"farm_uuid": [str(exc)]}) from exc
        return Response({"code": 200, "msg": "OK", "data": data}, status=status.HTTP_200_OK)


class Sensor7In1ComparisonChartView(Sensor7In1SummaryView):
    @extend_schema(tags=["Sensor 7 in 1"], parameters=[farm_uuid_query_param(required=True, description="UUID of the farm for sensor 7 in 1 comparison chart.")], responses={200: code_response("Sensor7In1ComparisonChartResponse", data=SoilComparisonChartSerializer())})
    def get(self, request):
        farm = self._get_farm(request)
        try:
            data = get_sensor_7_in_1_comparison_chart_data(farm)
        except DeviceDataUnavailableError as exc:
            raise serializers.ValidationError({"farm_uuid": [str(exc)]}) from exc
        return Response({"code": 200, "msg": "OK", "data": data}, status=status.HTTP_200_OK)


class SensorComparisonChartView(Sensor7In1SummaryView):
    @extend_schema(tags=["Sensor 7 in 1"], parameters=[farm_uuid_query_param(required=True, description="UUID of the farm."), OpenApiParameter(name="range", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False, description="Chart range, supported values: 7d, 30d. Defaults to 7d.")], responses={200: SensorComparisonChartResponseSerializer})
    def get(self, request):
        serializer = SensorComparisonChartQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        farm = self._get_farm(request)
        sensor = self._get_primary_sensor(farm=farm)
        try:
            data = get_sensor_comparison_chart_data(farm=farm, physical_device_uuid=sensor.physical_device_uuid, range_value=serializer.validated_data["range"])
        except DeviceDataUnavailableError as exc:
            raise serializers.ValidationError({"farm_uuid": [str(exc)]}) from exc
        return Response(data, status=status.HTTP_200_OK)


class SensorValuesListView(Sensor7In1SummaryView):
    @extend_schema(tags=["Sensor 7 in 1"], parameters=[farm_uuid_query_param(required=True, description="UUID of the farm."), OpenApiParameter(name="range", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False, description="Values list range, supported values: 1h, 24h, 7d. Defaults to 7d.")], responses={200: SensorValuesListResponseSerializer})
    def get(self, request):
        serializer = SensorValuesListQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        farm = self._get_farm(request)
        sensor = self._get_primary_sensor(farm=farm)
        try:
            data = get_sensor_values_list_data(farm=farm, physical_device_uuid=sensor.physical_device_uuid, range_value=serializer.validated_data["range"])
        except DeviceDataUnavailableError as exc:
            raise serializers.ValidationError({"farm_uuid": [str(exc)]}) from exc
        return Response(data, status=status.HTTP_200_OK)


class SensorRadarChartView(Sensor7In1SummaryView):
    @extend_schema(tags=["Sensor 7 in 1"], parameters=[farm_uuid_query_param(required=True, description="UUID of the farm."), OpenApiParameter(name="range", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False, description="Radar chart range, supported values: today, 7d, 30d. Defaults to 7d.")], responses={200: SensorRadarChartResponseSerializer})
    def get(self, request):
        serializer = SensorRadarChartQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        farm = self._get_farm(request)
        sensor = self._get_primary_sensor(farm=farm)
        try:
            data = get_sensor_radar_chart_data(farm=farm, physical_device_uuid=sensor.physical_device_uuid, range_value=serializer.validated_data["range"])
        except DeviceDataUnavailableError as exc:
            raise serializers.ValidationError({"farm_uuid": [str(exc)]}) from exc
        return Response(data, status=status.HTTP_200_OK)


class SensorExternalAPIView(APIView):
    authentication_classes = [SensorExternalAPIKeyAuthentication]
    permission_classes = [AllowAny]

    @extend_schema(tags=["Sensor External API"], request=SensorExternalRequestSerializer, examples=[OpenApiExample("Sensor External API Request", value={"uuid": "22222222-2222-2222-2222-222222222222", "payload": {"moisture_percent": 32.5, "temperature_c": 21.3, "ph": 6.7, "ec_ds_m": 1.1, "nitrogen_mg_kg": 42, "phosphorus_mg_kg": 18, "potassium_mg_kg": 210}}, request_only=True)], parameters=[OpenApiParameter(name="X-API-Key", type=OpenApiTypes.STR, location=OpenApiParameter.HEADER, required=True, default="12345", description="API key for sensor external API.")], responses={201: code_response("SensorExternalAPIResponse", data=FarmNotificationSerializer()), 401: code_response("SensorExternalAPIUnauthorizedResponse"), 404: code_response("SensorExternalAPIDeviceNotFoundResponse"), 503: code_response("SensorExternalAPIUnavailableResponse")})
    def post(self, request):
        serializer = SensorExternalRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            notification = create_sensor_external_notification(physical_device_uuid=serializer.validated_data["uuid"], payload=serializer.validated_data.get("payload"))
            forward_sensor_payload_to_farm_data(physical_device_uuid=serializer.validated_data["uuid"], payload=serializer.validated_data.get("payload"))
        except ValueError as exc:
            if "not migrated" in str(exc):
                return Response({"code": 503, "msg": "Required tables are not ready. Run migrations."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            return Response({"code": 404, "msg": "Physical device not found."}, status=status.HTTP_404_NOT_FOUND)
        except FarmDataForwardError as exc:
            return Response({"code": 503, "msg": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response({"code": 201, "msg": "success", "data": FarmNotificationSerializer(notification).data}, status=status.HTTP_201_CREATED)


class SensorExternalRequestLogListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = SensorExternalRequestLogPagination

    @extend_schema(tags=["Sensor External API"], parameters=[OpenApiParameter(name="farm_uuid", type=OpenApiTypes.UUID, location=OpenApiParameter.QUERY, required=True, default="11111111-1111-1111-1111-111111111111"), OpenApiParameter(name="page", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, required=True), OpenApiParameter(name="page_size", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, required=True), OpenApiParameter(name="physical_device_uuid", type=OpenApiTypes.UUID, location=OpenApiParameter.QUERY, required=False), OpenApiParameter(name="sensor_type", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False), OpenApiParameter(name="date_from", type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY, required=False), OpenApiParameter(name="date_to", type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY, required=False)], responses={200: code_response("SensorExternalRequestLogListResponse", data=SensorExternalRequestLogSerializer(many=True), extra_fields={"count": serializers.IntegerField(), "next": serializers.CharField(allow_null=True), "previous": serializers.CharField(allow_null=True)}), 401: code_response("SensorExternalRequestLogListUnauthorizedResponse"), 503: code_response("SensorExternalRequestLogListUnavailableResponse")})
    def get(self, request):
        serializer = SensorExternalRequestLogQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        try:
            queryset = get_sensor_external_request_logs_for_farm(farm_uuid=serializer.validated_data["farm_uuid"], physical_device_uuid=serializer.validated_data.get("physical_device_uuid"), sensor_type=serializer.validated_data.get("sensor_type"), date_from=serializer.validated_data.get("date_from"), date_to=serializer.validated_data.get("date_to"))
        except ValueError:
            return Response({"code": 503, "msg": "Required tables are not ready. Run migrations."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        paginator = self.pagination_class()
        paginator.page_size = serializer.validated_data["page_size"]
        page = paginator.paginate_queryset(queryset, request, view=self)
        farm_device_map = get_farm_device_map_for_logs(logs=page)
        data = SensorExternalRequestLogSerializer(page, many=True, context={"farm_device_map": farm_device_map}).data
        return Response({"code": 200, "msg": "success", "count": paginator.page.paginator.count, "next": paginator.get_next_link(), "previous": paginator.get_previous_link(), "data": data}, status=status.HTTP_200_OK)
