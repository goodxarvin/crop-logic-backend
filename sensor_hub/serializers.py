from rest_framework import serializers


class SensorStoreResponseSerializer(serializers.Serializer):
    """Schema for static sensor store response (name, uuid_sensor, last_updated, specifications, power_source, customized_sensors)."""

    name = serializers.CharField()
    uuid_sensor = serializers.CharField()
    last_updated = serializers.CharField()
    specifications = serializers.JSONField()
    power_source = serializers.JSONField()
    customized_sensors = serializers.JSONField()
