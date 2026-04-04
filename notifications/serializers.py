from rest_framework import serializers

from .models import FarmNotification


class FarmNotificationSerializer(serializers.ModelSerializer):
    farm_uuid = serializers.UUIDField(source="farm.farm_uuid", read_only=True)

    class Meta:
        model = FarmNotification
        fields = [
            "uuid",
            "farm_uuid",
            "title",
            "message",
            "level",
            "is_read",
            "metadata",
            "created_at",
        ]
