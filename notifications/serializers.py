from rest_framework import serializers


class NotificationPublishSerializer(serializers.Serializer):
    channel = serializers.CharField(max_length=128)
    title = serializers.CharField(max_length=255)
    message = serializers.CharField()
    level = serializers.ChoiceField(choices=["info", "success", "warning", "error"], default="info")
    metadata = serializers.DictField(required=False, default=dict)
    event = serializers.CharField(max_length=64, required=False, default="notification")
