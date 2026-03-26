from rest_framework import serializers


from .models import Sensor


class SensorSerializer(serializers.ModelSerializer):
    last_updated = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = Sensor
        fields = [
            "uuid_sensor",
            "name",
            "is_active",
            "specifications",
            "power_source",
            "customized_sensors",
            "last_updated",
        ]
        read_only_fields = ["uuid_sensor", "last_updated"]


class SensorCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sensor
        fields = [
            "name",
            "specifications",
            "power_source",
            "customized_sensors",
        ]


class SensorToggleSerializer(serializers.Serializer):
    uuid_sensor = serializers.UUIDField()
