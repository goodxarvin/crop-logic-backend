from rest_framework import serializers

from .models import DeviceCatalog, FarmDevice, SensorExternalRequestLog


class DeviceCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceCatalog
        fields = [
            "uuid",
            "code",
            "name",
            "description",
            "device_communication_type",
            "customizable_fields",
            "supported_power_sources",
            "returned_data_fields",
            "payload_mapping",
            "display_schema",
            "supported_widgets",
            "commands_schema",
            "capabilities",
            "sample_payload",
            "is_active",
        ]
        read_only_fields = fields


class SensorExternalRequestSerializer(serializers.Serializer):
    uuid = serializers.UUIDField()
    payload = serializers.JSONField(required=False, default=dict)


class SensorExternalRequestLogQuerySerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField()
    page = serializers.IntegerField(min_value=1)
    page_size = serializers.IntegerField(min_value=1, max_value=100)
    physical_device_uuid = serializers.UUIDField(required=False)
    sensor_type = serializers.CharField(required=False, allow_blank=False)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)

    def validate(self, attrs):
        date_from = attrs.get("date_from")
        date_to = attrs.get("date_to")
        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError({"date_to": "date_to must be greater than or equal to date_from."})
        return attrs


class FarmDeviceLogSerializer(serializers.ModelSerializer):
    sensor_catalog_uuid = serializers.UUIDField(source="sensor_catalog.uuid", read_only=True)
    device_catalogs = DeviceCatalogSerializer(many=True, read_only=True)

    class Meta:
        model = FarmDevice
        fields = [
            "uuid",
            "sensor_catalog_uuid",
            "device_catalogs",
            "physical_device_uuid",
            "name",
            "sensor_type",
            "is_active",
            "specifications",
            "power_source",
            "created_at",
            "updated_at",
        ]


class DeviceCatalogLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceCatalog
        fields = [
            "uuid",
            "code",
            "name",
            "description",
            "device_communication_type",
            "customizable_fields",
            "supported_power_sources",
            "returned_data_fields",
            "payload_mapping",
            "display_schema",
            "supported_widgets",
            "commands_schema",
            "capabilities",
            "sample_payload",
            "is_active",
            "created_at",
            "updated_at",
        ]


class DeviceDetailSerializer(serializers.ModelSerializer):
    device_catalog = DeviceCatalogSerializer(source="sensor_catalog", read_only=True)
    device_catalogs = serializers.SerializerMethodField()
    last_payload_at = serializers.SerializerMethodField()

    class Meta:
        model = FarmDevice
        fields = [
            "uuid",
            "physical_device_uuid",
            "name",
            "sensor_type",
            "is_active",
            "specifications",
            "power_source",
            "device_catalog",
            "device_catalogs",
            "last_payload_at",
            "created_at",
            "updated_at",
        ]

    def get_last_payload_at(self, obj):
        latest_log = self.context.get("latest_log")
        if latest_log is None:
            return None
        return latest_log.created_at

    def get_device_catalogs(self, obj):
        return DeviceCatalogSerializer(obj.get_device_catalogs(), many=True).data


class DeviceLatestPayloadSerializer(serializers.Serializer):
    physical_device_uuid = serializers.UUIDField()
    device_code = serializers.CharField()
    device_catalog_code = serializers.CharField(allow_blank=True, allow_null=True)
    raw_payload = serializers.JSONField()
    normalized_payload = serializers.JSONField()
    readings = serializers.JSONField()
    created_at = serializers.DateTimeField(allow_null=True)


class DeviceCommandRequestSerializer(serializers.Serializer):
    device_code = serializers.CharField()
    command = serializers.CharField()
    payload = serializers.JSONField(required=False, default=dict)


class DeviceCodeQuerySerializer(serializers.Serializer):
    device_code = serializers.CharField()


class DeviceRangeQuerySerializer(DeviceCodeQuerySerializer):
    range = serializers.CharField()


class DeviceCommandResponseSerializer(serializers.Serializer):
    physical_device_uuid = serializers.UUIDField()
    command = serializers.CharField()
    status = serializers.CharField()


class DeviceCodeListResponseSerializer(serializers.Serializer):
    physical_device_uuid = serializers.UUIDField()
    device_codes = serializers.ListField(child=serializers.CharField())


class SensorExternalRequestLogSerializer(serializers.ModelSerializer):
    farm_device = serializers.SerializerMethodField()
    sensor_catalog = serializers.SerializerMethodField()

    class Meta:
        model = SensorExternalRequestLog
        fields = [
            "id",
            "farm_uuid",
            "sensor_catalog_uuid",
            "physical_device_uuid",
            "farm_device",
            "sensor_catalog",
            "payload",
            "created_at",
        ]

    def get_farm_device(self, obj):
        farm_device_map = self.context.get("farm_device_map", {})
        farm_device = farm_device_map.get(
            (obj.farm_uuid, obj.sensor_catalog_uuid, obj.physical_device_uuid)
        ) or farm_device_map.get((obj.farm_uuid, None, obj.physical_device_uuid))
        if farm_device is None:
            return None
        return FarmDeviceLogSerializer(farm_device).data

    def get_sensor_catalog(self, obj):
        farm_device_map = self.context.get("farm_device_map", {})
        farm_device = farm_device_map.get(
            (obj.farm_uuid, obj.sensor_catalog_uuid, obj.physical_device_uuid)
        ) or farm_device_map.get((obj.farm_uuid, None, obj.physical_device_uuid))
        if farm_device is None or farm_device.sensor_catalog is None:
            return None
        return DeviceCatalogLogSerializer(farm_device.sensor_catalog).data
