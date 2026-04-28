from rest_framework import serializers

from notifications.serializers import FarmNotificationSerializer


ALLOWED_TRACKER_FIELDS = {"farm_uuid", "alerts"}


class FarmAlertInputSerializer(serializers.Serializer):
    alert_id = serializers.CharField(required=False, allow_blank=True)
    level = serializers.CharField(required=False, allow_blank=True)
    title = serializers.CharField(required=False, allow_blank=True)
    message = serializers.CharField(required=False, allow_blank=True)
    suggested_action = serializers.CharField(required=False, allow_blank=True)
    source_metric_type = serializers.CharField(required=False, allow_blank=True)
    timestamp = serializers.DateTimeField(required=False, allow_null=True)
    payload = serializers.JSONField(required=False)


class FarmAlertsTrackerRequestSerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField(required=True, help_text="UUID مزرعه.")
    alerts = FarmAlertInputSerializer(many=True, required=False, default=list)

    def validate(self, attrs):
        initial_keys = set(getattr(self, "initial_data", {}).keys())
        extra_fields = initial_keys - ALLOWED_TRACKER_FIELDS
        if extra_fields:
            raise serializers.ValidationError(
                {field: ["This field is not allowed."] for field in sorted(extra_fields)}
            )
        return attrs


class AlertTrackerAIResponseSerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField(read_only=True)
    service_id = serializers.CharField()
    tracker = serializers.JSONField()
    headline = serializers.CharField(allow_blank=True)
    overview = serializers.CharField(allow_blank=True)
    status_level = serializers.CharField()
    notifications = FarmNotificationSerializer(many=True)
    raw_llm_response = serializers.CharField(allow_blank=True)
    structured_context = serializers.JSONField()


class AlertStatSerializer(serializers.Serializer):
    title = serializers.CharField()
    count = serializers.CharField()
    avatarColor = serializers.CharField()
    avatarIcon = serializers.CharField()


class AlertTrackerSerializer(serializers.Serializer):
    totalAlerts = serializers.IntegerField()
    radialBarValue = serializers.IntegerField()
    alertStats = AlertStatSerializer(many=True)


class AlertTimelineItemSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.CharField()
    time = serializers.CharField()
    color = serializers.CharField()


class AlertTimelineSerializer(serializers.Serializer):
    alerts = AlertTimelineItemSerializer(many=True)


class AnomalyItemSerializer(serializers.Serializer):
    sensor = serializers.CharField()
    value = serializers.CharField()
    expected = serializers.CharField()
    deviation = serializers.CharField()
    severity = serializers.CharField()


class AnomalyDetectionSerializer(serializers.Serializer):
    anomalies = AnomalyItemSerializer(many=True)


class RecommendationItemSerializer(serializers.Serializer):
    title = serializers.CharField()
    subtitle = serializers.CharField()
    avatarIcon = serializers.CharField()
    avatarColor = serializers.CharField()


class RecommendationsListSerializer(serializers.Serializer):
    recommendations = RecommendationItemSerializer(many=True)


class CreateAlertSerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField(required=False, allow_null=True, help_text="UUID مزرعه برای اتصال alert به مزرعه.")
    title = serializers.CharField(max_length=255, help_text="عنوان هشدار.")
    description = serializers.CharField(required=False, default="", allow_blank=True, help_text="توضیح هشدار.")
    color = serializers.ChoiceField(choices=["info", "warning", "error", "success"], default="info", help_text="سطح یا رنگ هشدار.")
    avatar_icon = serializers.CharField(required=False, default="", allow_blank=True, help_text="آیکون هشدار.")
    avatar_color = serializers.CharField(required=False, default="", allow_blank=True, help_text="رنگ آواتار هشدار.")
