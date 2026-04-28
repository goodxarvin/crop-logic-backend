from rest_framework import serializers

from farm_hub.models import FarmSensor
from sensor_catalog.models import SensorCatalog

from .models import SensorExternalRequestLog


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


class SensorExternalRequestLogSerializer(serializers.ModelSerializer):
    farm_sensor = serializers.SerializerMethodField()
    sensor_catalog = serializers.SerializerMethodField()

    class Meta:
        model = SensorExternalRequestLog
        fields = [
            "id",
            "farm_uuid",
            "sensor_catalog_uuid",
            "physical_device_uuid",
            "farm_sensor",
            "sensor_catalog",
            "payload",
            "created_at",
        ]

    def get_farm_sensor(self, obj):
        farm_sensor_map = self.context.get("farm_sensor_map", {})
        farm_sensor = farm_sensor_map.get(
            (obj.farm_uuid, obj.sensor_catalog_uuid, obj.physical_device_uuid)
        ) or farm_sensor_map.get((obj.farm_uuid, None, obj.physical_device_uuid))
        if farm_sensor is None:
            return None
        return FarmSensorLogSerializer(farm_sensor).data

    def get_sensor_catalog(self, obj):
        farm_sensor_map = self.context.get("farm_sensor_map", {})
        farm_sensor = farm_sensor_map.get(
            (obj.farm_uuid, obj.sensor_catalog_uuid, obj.physical_device_uuid)
        ) or farm_sensor_map.get((obj.farm_uuid, None, obj.physical_device_uuid))
        if farm_sensor is None or farm_sensor.sensor_catalog is None:
            return None
        return SensorCatalogLogSerializer(farm_sensor.sensor_catalog).data


class FarmSensorLogSerializer(serializers.ModelSerializer):
    sensor_catalog_uuid = serializers.UUIDField(source="sensor_catalog.uuid", read_only=True)

    class Meta:
        model = FarmSensor
        fields = [
            "uuid",
            "sensor_catalog_uuid",
            "physical_device_uuid",
            "name",
            "sensor_type",
            "is_active",
            "specifications",
            "power_source",
            "created_at",
            "updated_at",
        ]


class SensorCatalogLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorCatalog
        fields = [
            "uuid",
            "code",
            "name",
            "description",
            "customizable_fields",
            "supported_power_sources",
            "returned_data_fields",
            "sample_payload",
            "is_active",
            "created_at",
            "updated_at",
        ]
