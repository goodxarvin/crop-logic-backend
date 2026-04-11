from rest_framework import serializers


class HealthDataItemSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, allow_blank=True)
    value = serializers.CharField(required=False, allow_blank=True)
    color = serializers.CharField(required=False, allow_blank=True)
    icon = serializers.CharField(required=False, allow_blank=True)


class NdviHealthCardSerializer(serializers.Serializer):
    ndviIndex = serializers.FloatField(required=False)
    healthData = HealthDataItemSerializer(many=True, required=False)


class FarmHealthScoreSerializer(serializers.Serializer):
    id = serializers.CharField(required=False, allow_blank=True)
    title = serializers.CharField(required=False, allow_blank=True)
    subtitle = serializers.CharField(required=False, allow_blank=True)
    stats = serializers.CharField(required=False, allow_blank=True)
    avatarColor = serializers.CharField(required=False, allow_blank=True)
    avatarIcon = serializers.CharField(required=False, allow_blank=True)
    chipText = serializers.CharField(required=False, allow_blank=True)
    chipColor = serializers.CharField(required=False, allow_blank=True)


class CropHealthSummarySerializer(serializers.Serializer):
    ndviHealthCard = NdviHealthCardSerializer(required=False)
    farmHealthScore = FarmHealthScoreSerializer(required=False)
