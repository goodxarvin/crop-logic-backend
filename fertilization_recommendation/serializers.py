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


class NpkRatioSerializer(serializers.Serializer):
    n = serializers.FloatField(required=False)
    p = serializers.FloatField(required=False)
    k = serializers.FloatField(required=False)
    label = serializers.CharField(required=False, allow_blank=True)


class ApplicationMethodSerializer(serializers.Serializer):
    id = serializers.CharField(required=False, allow_blank=True)
    label = serializers.CharField(required=False, allow_blank=True)


class ApplicationIntervalSerializer(serializers.Serializer):
    value = serializers.FloatField(required=False)
    unit = serializers.CharField(required=False, allow_blank=True)
    label = serializers.CharField(required=False, allow_blank=True)


class DosageSerializer(serializers.Serializer):
    base_amount_per_hectare = serializers.FloatField(required=False)
    base_amount_per_square_meter = serializers.FloatField(required=False)
    unit = serializers.CharField(required=False, allow_blank=True)
    label = serializers.CharField(required=False, allow_blank=True)
    calculation_basis = serializers.CharField(required=False, allow_blank=True)


class PrimaryRecommendationSerializer(serializers.Serializer):
    fertilizer_code = serializers.CharField(required=False, allow_blank=True)
    fertilizer_name = serializers.CharField(required=False, allow_blank=True)
    display_title = serializers.CharField(required=False, allow_blank=True)
    fertilizer_type = serializers.CharField(required=False, allow_blank=True)
    npk_ratio = NpkRatioSerializer(required=False)
    application_method = ApplicationMethodSerializer(required=False)
    application_interval = ApplicationIntervalSerializer(required=False)
    dosage = DosageSerializer(required=False)
    reasoning = serializers.CharField(required=False, allow_blank=True)
    summary = serializers.CharField(required=False, allow_blank=True)


class NutrientItemSerializer(serializers.Serializer):
    key = serializers.CharField(required=False, allow_blank=True)
    name = serializers.CharField(required=False, allow_blank=True)
    value = serializers.FloatField(required=False)
    unit = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)


class NutrientAnalysisSerializer(serializers.Serializer):
    macro = NutrientItemSerializer(many=True, read_only=True)
    micro = NutrientItemSerializer(many=True, read_only=True)


class ApplicationGuideStepSerializer(serializers.Serializer):
    step_number = serializers.IntegerField(required=False)
    title = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)


class ApplicationGuideSerializer(serializers.Serializer):
    safety_warning = serializers.CharField(required=False, allow_blank=True)
    steps = ApplicationGuideStepSerializer(many=True, read_only=True)


class AlternativeRecommendationSerializer(serializers.Serializer):
    fertilizer_code = serializers.CharField(required=False, allow_blank=True)
    fertilizer_name = serializers.CharField(required=False, allow_blank=True)
    fertilizer_type = serializers.CharField(required=False, allow_blank=True)
    usage_method = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)


class FertilizationRecommendResponseDataSerializer(serializers.Serializer):
    primary_recommendation = PrimaryRecommendationSerializer(read_only=True)
    nutrient_analysis = NutrientAnalysisSerializer(read_only=True)
    application_guide = ApplicationGuideSerializer(read_only=True)
    alternative_recommendations = AlternativeRecommendationSerializer(many=True, read_only=True)
    sections = FertilizationSectionSerializer(many=True, read_only=True)
