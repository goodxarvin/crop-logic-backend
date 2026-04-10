from rest_framework import serializers


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
    farm_uuid = serializers.UUIDField(required=False, allow_null=True)
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, default="", allow_blank=True)
    color = serializers.ChoiceField(choices=["info", "warning", "error", "success"], default="info")
    avatar_icon = serializers.CharField(required=False, default="", allow_blank=True)
    avatar_color = serializers.CharField(required=False, default="", allow_blank=True)
