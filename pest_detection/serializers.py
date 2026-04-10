from rest_framework import serializers


class RiskDetailsSerializer(serializers.Serializer):
    risk_level = serializers.CharField(required=False, allow_blank=True)
    risk_percentage = serializers.IntegerField(required=False)
    detected_diseases = serializers.ListField(child=serializers.DictField(), required=False)
    detected_pests = serializers.ListField(child=serializers.DictField(), required=False)
    last_assessed_at = serializers.CharField(required=False, allow_blank=True)
    recommendation = serializers.CharField(required=False, allow_blank=True)


class RiskCardSerializer(serializers.Serializer):
    id = serializers.CharField(required=False, allow_blank=True)
    title = serializers.CharField(required=False, allow_blank=True)
    subtitle = serializers.CharField(required=False, allow_blank=True)
    stats = serializers.CharField(required=False, allow_blank=True)
    avatarColor = serializers.CharField(required=False, allow_blank=True)
    avatarIcon = serializers.CharField(required=False, allow_blank=True)
    chipText = serializers.CharField(required=False, allow_blank=True)
    chipColor = serializers.CharField(required=False, allow_blank=True)
    details = RiskDetailsSerializer(required=False)


class RiskSummaryDataSerializer(serializers.Serializer):
    disease_risk = RiskCardSerializer(required=False)
    pest_risk = RiskCardSerializer(required=False)
