from rest_framework import serializers


class SensorExternalRequestSerializer(serializers.Serializer):
    payload = serializers.JSONField(required=False, default=dict)
