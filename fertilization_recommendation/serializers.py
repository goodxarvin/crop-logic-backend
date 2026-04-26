from rest_framework import serializers


class FertilizationFarmDataSerializer(serializers.Serializer):
    soilType = serializers.CharField(required=False, allow_blank=True)
    organicMatter = serializers.CharField(required=False, allow_blank=True)
    waterEC = serializers.CharField(required=False, allow_blank=True)


class FertilizationRecommendRequestSerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField(required=True, help_text="UUID مزرعه برای دریافت توصیه کودی.")
    plant_name = serializers.CharField(required=False, allow_blank=True, help_text="نام محصول یا گیاه.")
    growth_stage = serializers.CharField(required=False, allow_blank=True, help_text="مرحله رشد گیاه.")


class FertilizationSectionSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["text", "list", "recommendation", "warning"])
    title = serializers.CharField(required=False, allow_blank=True)
    icon = serializers.CharField(required=False, allow_blank=True)
    content = serializers.CharField(required=False, allow_blank=True)
    items = serializers.ListField(child=serializers.CharField(), required=False)
    fertilizerType = serializers.CharField(required=False, allow_blank=True)
    amount = serializers.CharField(required=False, allow_blank=True)
    applicationMethod = serializers.CharField(required=False, allow_blank=True)
    timing = serializers.CharField(required=False, allow_blank=True)
    validityPeriod = serializers.CharField(required=False, allow_blank=True)
    expandableExplanation = serializers.CharField(required=False, allow_blank=True)


class FertilizationRecommendResponseDataSerializer(serializers.Serializer):
    sections = FertilizationSectionSerializer(many=True, read_only=True)
