from rest_framework import serializers


class PestDetectionAnalyzeRequestSerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField(required=True, help_text="UUID مزرعه برای تحلیل آفت/بیماری.")
    sensor_uuid = serializers.UUIDField(required=False, help_text="UUID سنسور مرتبط در صورت وجود.")
    plant_name = serializers.CharField(required=False, allow_blank=True, default="", help_text="نام گیاه یا محصول.")
    query = serializers.CharField(required=False, allow_blank=True, default="", help_text="پرسش یا توضیح متنی کاربر.")
    image_urls = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
    )
    image = serializers.CharField(required=False, allow_blank=True, default="")
    images = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
    )

    def validate(self, attrs):
        attrs["query"] = (attrs.get("query") or "").strip()
        attrs["plant_name"] = (attrs.get("plant_name") or "").strip()
        return attrs


class PestDetectionAnalyzeResponseSerializer(serializers.Serializer):
    has_issue = serializers.BooleanField(required=False)
    category = serializers.CharField(required=False, allow_blank=True)
    confidence = serializers.FloatField(required=False)
    severity = serializers.CharField(required=False, allow_blank=True)
    summary = serializers.CharField(required=False, allow_blank=True)
    detected_signs = serializers.ListField(child=serializers.CharField(), required=False)
    possible_causes = serializers.ListField(child=serializers.CharField(), required=False)
    immediate_actions = serializers.ListField(child=serializers.CharField(), required=False)
    reasoning = serializers.ListField(child=serializers.CharField(), required=False)


class PestDetectionRiskRequestSerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField(default="11111111-1111-1111-1111-111111111111", help_text="UUID مزرعه برای تحلیل ریسک آفت/بیماری.")
    plant_name = serializers.CharField(required=False, allow_blank=True, default="پیاز", help_text="نام محصول یا گیاه.")
    growth_stage = serializers.CharField(required=False, allow_blank=True, default="گلدهی", help_text="مرحله رشد گیاه.")


class PestDetectionRiskSummaryRequestSerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField(required=True, help_text="UUID مزرعه برای خلاصه ریسک آفت/بیماری.")


class RiskBreakdownSerializer(serializers.Serializer):
    score = serializers.FloatField(required=False)
    level = serializers.CharField(required=False, allow_blank=True)
    likely_conditions = serializers.ListField(child=serializers.CharField(), required=False)
    reasoning = serializers.ListField(child=serializers.CharField(), required=False)


class PestDetectionRiskResponseSerializer(serializers.Serializer):
    summary = serializers.CharField(required=False, allow_blank=True)
    forecast_window = serializers.CharField(required=False, allow_blank=True)
    overall_risk = serializers.CharField(required=False, allow_blank=True)
    disease_risk = RiskBreakdownSerializer(required=False)
    pest_risk = RiskBreakdownSerializer(required=False)
    key_drivers = serializers.ListField(child=serializers.CharField(), required=False)
    recommended_actions = serializers.ListField(child=serializers.CharField(), required=False)


class RiskCardSerializer(serializers.Serializer):
    id = serializers.CharField(required=False, allow_blank=True)
    title = serializers.CharField(required=False, allow_blank=True)
    subtitle = serializers.CharField(required=False, allow_blank=True)
    stats = serializers.CharField(required=False, allow_blank=True)
    avatarColor = serializers.CharField(required=False, allow_blank=True)
    avatarIcon = serializers.CharField(required=False, allow_blank=True)
    chipText = serializers.CharField(required=False, allow_blank=True)
    chipColor = serializers.CharField(required=False, allow_blank=True)
    details = serializers.DictField(required=False)


class PestDetectionRiskSummaryResponseSerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField(required=False, allow_null=True)
    diseaseRisk = RiskCardSerializer(required=False)
    pestRisk = RiskCardSerializer(required=False)
    drivers = serializers.DictField(required=False)
