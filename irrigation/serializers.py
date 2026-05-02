from rest_framework import serializers


class IrrigationFarmDataSerializer(serializers.Serializer):
    soilType = serializers.CharField(required=False, allow_blank=True)
    waterQuality = serializers.CharField(required=False, allow_blank=True)
    climateZone = serializers.CharField(required=False, allow_blank=True)


class IrrigationRecommendRequestSerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField(required=False, help_text="UUID مزرعه برای دریافت توصیه آبیاری.")
    sensor_uuid = serializers.UUIDField(required=False, help_text="نام قدیمی farm_uuid برای سازگاری با کلاینت های قدیمی.")
    plant_name = serializers.CharField(required=False, allow_blank=True, help_text="نام محصول یا گیاه.")
    growth_stage = serializers.CharField(required=False, allow_blank=True, help_text="مرحله رشد گیاه.")
    irrigation_type = serializers.CharField(required=False, allow_blank=True, help_text="نام روش آبیاری مورد استفاده در UI.")
    irrigation_method_name = serializers.CharField(required=False, allow_blank=True, help_text="نام روش آبیاری انتخابی.")

    def validate(self, attrs):
        farm_uuid = attrs.get("farm_uuid") or attrs.get("sensor_uuid")
        if not farm_uuid:
            raise serializers.ValidationError({"farm_uuid": ["This field is required."]})

        attrs["farm_uuid"] = farm_uuid
        irrigation_method_name = attrs.get("irrigation_method_name") or attrs.get("irrigation_type")
        if irrigation_method_name:
            attrs["irrigation_method_name"] = irrigation_method_name
            attrs.setdefault("irrigation_type", irrigation_method_name)

        return attrs


class WaterStressRequestSerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField(required=True, help_text="UUID مزرعه برای محاسبه تنش آبی.")
    sensor_uuid = serializers.UUIDField(required=False, help_text="UUID سنسور برای فیلتر اختیاری.")


class IrrigationMethodSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    name = serializers.CharField(required=False, allow_blank=True)
    category = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    water_efficiency_percent = serializers.FloatField(required=False)
    water_pressure_required = serializers.CharField(required=False, allow_blank=True)
    flow_rate = serializers.CharField(required=False, allow_blank=True)
    coverage_area = serializers.CharField(required=False, allow_blank=True)
    soil_type = serializers.CharField(required=False, allow_blank=True)
    climate_suitability = serializers.CharField(required=False, allow_blank=True)
    created_at = serializers.DateTimeField(required=False)
    updated_at = serializers.DateTimeField(required=False)


class IrrigationRecommendationListQuerySerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField(required=True, help_text="UUID مزرعه برای دریافت لیست توصیه های آبیاری.")
    page = serializers.IntegerField(required=False, min_value=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100)


class IrrigationRecommendationListItemSerializer(serializers.Serializer):
    recommendation_uuid = serializers.UUIDField(source="uuid", read_only=True)
    crop_id = serializers.CharField(read_only=True)
    plant_name = serializers.CharField(source="crop_id", read_only=True)
    growth_stage = serializers.CharField(read_only=True)
    irrigation_method_name = serializers.CharField(read_only=True, allow_blank=True)
    status = serializers.CharField(read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    requested_at = serializers.DateTimeField(source="created_at", read_only=True)


class FreeTextPlanParserRequestSerializer(serializers.Serializer):
    message = serializers.CharField(required=False, allow_blank=True, help_text="متن آزاد کاربر.")
    answers = serializers.DictField(required=False, help_text="پاسخ های تکمیلی کاربر.")
    partial_plan = serializers.DictField(required=False, help_text="داده استخراج شده از مرحله قبل.")
    farm_uuid = serializers.UUIDField(
        required=False,
        allow_null=True,
        initial="11111111-1111-1111-1111-111111111111",
        help_text="UUID مزرعه برای context اختیاری.",
    )

    def validate(self, attrs):
        has_message = bool((attrs.get("message") or "").strip())
        has_answers = isinstance(attrs.get("answers"), dict) and bool(attrs.get("answers"))
        has_partial_plan = isinstance(attrs.get("partial_plan"), dict) and bool(attrs.get("partial_plan"))
        if not (has_message or has_answers or has_partial_plan):
            raise serializers.ValidationError(
                {"non_field_errors": ["حداقل یکی از message، answers یا partial_plan باید ارسال شود."]}
            )
        return attrs


class PlanParserQuestionSerializer(serializers.Serializer):
    id = serializers.CharField(required=False, allow_blank=True)
    field = serializers.CharField(required=False, allow_blank=True)
    question = serializers.CharField(required=False, allow_blank=True)
    rationale = serializers.CharField(required=False, allow_blank=True)


class FreeTextPlanParserResponseDataSerializer(serializers.Serializer):
    status = serializers.CharField(required=False, allow_blank=True)
    status_fa = serializers.CharField(required=False, allow_blank=True)
    summary = serializers.CharField(required=False, allow_blank=True)
    missing_fields = serializers.ListField(child=serializers.CharField(), required=False)
    questions = PlanParserQuestionSerializer(many=True, required=False)
    collected_data = serializers.DictField(required=False)
    final_plan = serializers.DictField(required=False, allow_null=True)


class IrrigationRecommendResponseDataSerializer(serializers.Serializer):
    recommendation_uuid = serializers.UUIDField(read_only=True, required=False)
    crop_id = serializers.CharField(read_only=True, required=False, allow_blank=True)
    plant_name = serializers.CharField(read_only=True, required=False, allow_blank=True)
    growth_stage = serializers.CharField(read_only=True, required=False, allow_blank=True)
    irrigation_method_name = serializers.CharField(read_only=True, required=False, allow_blank=True)
    status = serializers.CharField(read_only=True, required=False)
    status_label = serializers.CharField(read_only=True, required=False)
    plan = serializers.DictField(read_only=True)
    water_balance = serializers.DictField(read_only=True)
    timeline = serializers.ListField(child=serializers.DictField(), read_only=True)
    sections = serializers.ListField(child=serializers.DictField(), read_only=True)


class IrrigationPlanListQuerySerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField(required=True, help_text="UUID مزرعه برای دریافت لیست برنامه های آبیاری.")
    page = serializers.IntegerField(required=False, min_value=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100)


class IrrigationPlanListItemSerializer(serializers.Serializer):
    plan_uuid = serializers.UUIDField(source="uuid", read_only=True)
    source = serializers.CharField(read_only=True)
    source_label = serializers.CharField(source="get_source_display", read_only=True)
    title = serializers.CharField(read_only=True)
    crop_id = serializers.CharField(read_only=True)
    plant_name = serializers.CharField(source="crop_id", read_only=True)
    growth_stage = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class IrrigationPlanDetailSerializer(serializers.Serializer):
    plan_uuid = serializers.UUIDField(source="uuid", read_only=True)
    source = serializers.CharField(read_only=True)
    source_label = serializers.CharField(source="get_source_display", read_only=True)
    title = serializers.CharField(read_only=True)
    crop_id = serializers.CharField(read_only=True)
    plant_name = serializers.CharField(source="crop_id", read_only=True)
    growth_stage = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    plan_payload = serializers.DictField(read_only=True)


class IrrigationPlanStatusUpdateSerializer(serializers.Serializer):
    is_active = serializers.BooleanField(required=True)
