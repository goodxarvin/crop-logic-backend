from rest_framework import serializers


class FertilizationFarmDataSerializer(serializers.Serializer):
    soilType = serializers.CharField(required=False, allow_blank=True)
    organicMatter = serializers.CharField(required=False, allow_blank=True)
    waterEC = serializers.CharField(required=False, allow_blank=True)


class FertilizationRecommendRequestSerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField(required=True, help_text="UUID مزرعه برای دریافت توصیه کودی.")
    crop_id = serializers.CharField(required=False, allow_blank=True, help_text="شناسه یا نام محصول. این فیلد همان plant_name است.")
    plant_name = serializers.CharField(required=False, allow_blank=True, help_text="نام محصول یا گیاه. این فیلد همان crop_id است.")
    growth_stage = serializers.CharField(required=False, allow_blank=True, help_text="مرحله رشد گیاه.")


class FertilizationRecommendationListQuerySerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField(required=True, help_text="UUID مزرعه برای دریافت لیست توصیه های کودی.")
    page = serializers.IntegerField(required=False, min_value=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100)


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


class FertilizationRecommendationListItemSerializer(serializers.Serializer):
    recommendation_uuid = serializers.UUIDField(source="uuid", read_only=True)
    crop_id = serializers.CharField(read_only=True)
    plant_name = serializers.CharField(source="crop_id", read_only=True)
    growth_stage = serializers.CharField(read_only=True)
    fertilizer_type = serializers.CharField(read_only=True, allow_blank=True)
    status = serializers.CharField(read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    requested_at = serializers.DateTimeField(source="created_at", read_only=True)


class FertilizationRecommendResponseDataSerializer(serializers.Serializer):
    recommendation_uuid = serializers.UUIDField(read_only=True, required=False)
    crop_id = serializers.CharField(read_only=True, required=False, allow_blank=True)
    plant_name = serializers.CharField(read_only=True, required=False, allow_blank=True)
    growth_stage = serializers.CharField(read_only=True, required=False, allow_blank=True)
    status = serializers.CharField(read_only=True, required=False)
    status_label = serializers.CharField(read_only=True, required=False)
    primary_recommendation = PrimaryRecommendationSerializer(read_only=True)
    nutrient_analysis = NutrientAnalysisSerializer(read_only=True)
    application_guide = ApplicationGuideSerializer(read_only=True)
    alternative_recommendations = AlternativeRecommendationSerializer(many=True, read_only=True)
    sections = FertilizationSectionSerializer(many=True, read_only=True)
