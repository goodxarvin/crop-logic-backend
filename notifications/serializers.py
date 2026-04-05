from rest_framework import serializers

from .models import FarmNotification


class FarmNotificationSerializer(serializers.ModelSerializer):
    farm_uuid = serializers.UUIDField(source="farm.farm_uuid", read_only=True)
    since_id = serializers.IntegerField(source="id", read_only=True)

    class Meta:
        model = FarmNotification
        fields = [
            "uuid",
            "farm_uuid",
            "since_id",
            "title",
            "message",
            "level",
            "is_read",
            "metadata",
            "created_at",
        ]
