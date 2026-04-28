from rest_framework import serializers

from .models import FarmNotification


class FarmNotificationSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    farm_uuid = serializers.UUIDField(source="farm.farm_uuid", read_only=True)
    since_id = serializers.IntegerField(source="id", read_only=True)

    class Meta:
        model = FarmNotification
        fields = [
            "id",
            "uuid",
            "farm_uuid",
            "since_id",
            "endpoint",
            "title",
            "message",
            "level",
            "suggested_action",
            "source_alert_id",
            "source_metric_type",
            "payload",
            "is_read",
            "metadata",
            "created_at",
            "updated_at",
        ]
