from rest_framework import serializers

def success_response():
    return {"status": "success"}


def success_with_data(data):
    return {"status": "success", "data": data}


class YieldPredictionCardSerializer(serializers.Serializer):
    id = serializers.CharField(required=False, allow_blank=True)
    title = serializers.CharField(required=False, allow_blank=True)
    subtitle = serializers.CharField(required=False, allow_blank=True)
    stats = serializers.CharField(required=False, allow_blank=True)
    avatarColor = serializers.CharField(required=False, allow_blank=True)
    avatarIcon = serializers.CharField(required=False, allow_blank=True)
    chipText = serializers.CharField(required=False, allow_blank=True)
    chipColor = serializers.CharField(required=False, allow_blank=True)


class ChartSeriesSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True)
    data = serializers.ListField(child=serializers.FloatField(), required=False)


class ChartSummaryItemSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, allow_blank=True)
    subtitle = serializers.CharField(required=False, allow_blank=True)
    amount = serializers.CharField(required=False, allow_blank=True)
    avatarColor = serializers.CharField(required=False, allow_blank=True)
    avatarIcon = serializers.CharField(required=False, allow_blank=True)


class YieldPredictionChartSerializer(serializers.Serializer):
    categories = serializers.ListField(child=serializers.CharField(), required=False)
    series = ChartSeriesSerializer(many=True, required=False)
    summary = ChartSummaryItemSerializer(many=True, required=False)


class HarvestPredictionCardSerializer(serializers.Serializer):
    date = serializers.CharField(required=False, allow_blank=True)
    dateFormatted = serializers.CharField(required=False, allow_blank=True)
    daysUntil = serializers.IntegerField(required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    optimalWindowStart = serializers.CharField(required=False, allow_blank=True)
    optimalWindowEnd = serializers.CharField(required=False, allow_blank=True)


class YieldHarvestSummarySerializer(serializers.Serializer):
    yield_prediction_card = YieldPredictionCardSerializer(required=False)
    yield_prediction_chart = YieldPredictionChartSerializer(required=False)
    harvest_prediction_card = HarvestPredictionCardSerializer(required=False)


class CropSimulationRequestSerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField(required=True, help_text="UUID مزرعه برای اجرای شبیه‌سازی.")
    plant_name = serializers.CharField(required=False, allow_blank=True, default="", help_text="نام گیاه یا محصول.")


class GrowthSimulationRequestSerializer(serializers.Serializer):
    plant_name = serializers.CharField(required=True, help_text="نام گیاه برای شروع شبیه‌سازی رشد.")
    dynamic_parameters = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        allow_empty=False,
        help_text="لیست پارامترهای دینامیک موردنیاز مانند DVS یا LAI.",
    )
    farm_uuid = serializers.UUIDField(required=False, allow_null=True, help_text="UUID مزرعه؛ در صورت نبود باید weather ارسال شود.")
    weather = serializers.JSONField(required=False, help_text="آب‌وهوا به‌صورت object یا array.")
    soil_parameters = serializers.DictField(required=False, help_text="پارامترهای خاک.")
    site_parameters = serializers.DictField(required=False, help_text="پارامترهای سایت.")
    crop_parameters = serializers.DictField(required=False, help_text="پارامترهای محصول.")
    agromanagement = serializers.DictField(required=False, help_text="تنظیمات مدیریت زراعی.")
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=50, help_text="اندازه صفحه بین 1 تا 50.")

    def validate(self, attrs):
        if not attrs.get("farm_uuid") and attrs.get("weather") in (None, "", [], {}):
            raise serializers.ValidationError("At least one of 'farm_uuid' or 'weather' must be provided.")
        return attrs


class GrowthSimulationQueuedDataSerializer(serializers.Serializer):
    task_id = serializers.CharField(required=False, allow_blank=True, help_text="شناسه تسک شبیه‌سازی رشد.")
    status_url = serializers.CharField(required=False, allow_blank=True, help_text="آدرس بررسی وضعیت تسک.")
    plant_name = serializers.CharField(required=False, allow_blank=True, help_text="نام گیاه شبیه‌سازی‌شده.")


class GrowthSimulationProgressSerializer(serializers.Serializer):
    current = serializers.IntegerField(required=False, help_text="مرحله فعلی پیشرفت.")
    total = serializers.IntegerField(required=False, help_text="تعداد کل مراحل.")
    percent = serializers.FloatField(required=False, help_text="درصد پیشرفت.")


class GrowthSimulationPaginationSerializer(serializers.Serializer):
    page = serializers.IntegerField(required=False, help_text="شماره صفحه فعلی.")
    page_size = serializers.IntegerField(required=False, help_text="اندازه صفحه.")
    total_items = serializers.IntegerField(required=False, help_text="تعداد کل آیتم‌ها.")
    total_pages = serializers.IntegerField(required=False, help_text="تعداد کل صفحات.")
    has_next = serializers.BooleanField(required=False, help_text="آیا صفحه بعدی وجود دارد.")
    has_previous = serializers.BooleanField(required=False, help_text="آیا صفحه قبلی وجود دارد.")


class GrowthSimulationResultSerializer(serializers.Serializer):
    plant_name = serializers.CharField(required=False, allow_blank=True)
    dynamic_parameters = serializers.ListField(child=serializers.CharField(), required=False)
    engine = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    model_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    scenario_id = serializers.IntegerField(required=False)
    simulation_warning = serializers.CharField(required=False, allow_blank=True)
    summary_metrics = serializers.DictField(required=False)
    stage_timeline = serializers.ListField(child=serializers.DictField(), required=False)
    stages_page = serializers.ListField(child=serializers.DictField(), required=False)
    pagination = GrowthSimulationPaginationSerializer(required=False)
    daily_records_count = serializers.IntegerField(required=False)
    default_page_size = serializers.IntegerField(required=False)


class GrowthSimulationStatusDataSerializer(serializers.Serializer):
    task_id = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False, allow_blank=True)
    message = serializers.CharField(required=False, allow_blank=True)
    progress = GrowthSimulationProgressSerializer(required=False)
    result = GrowthSimulationResultSerializer(required=False)
    error = serializers.CharField(required=False, allow_blank=True)


class CurrentFarmChartSerializer(serializers.Serializer):
    farm_uuid = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    plant_name = serializers.CharField(required=False, allow_blank=True)
    engine = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    model_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    scenario_id = serializers.IntegerField(required=False)
    simulation_warning = serializers.CharField(required=False, allow_blank=True)
    categories = serializers.ListField(child=serializers.CharField(), required=False)
    series = serializers.DictField(required=False)
    summary = serializers.DictField(required=False)
    current_state = serializers.DictField(required=False)
    metrics = serializers.DictField(required=False)
    daily_output = serializers.DictField(required=False)


class HarvestPredictionSerializer(serializers.Serializer):
    date = serializers.CharField(required=False, allow_blank=True)
    dateFormatted = serializers.CharField(required=False, allow_blank=True)
    daysUntil = serializers.IntegerField(required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    optimalWindowStart = serializers.CharField(required=False, allow_blank=True)
    optimalWindowEnd = serializers.CharField(required=False, allow_blank=True)
    gddDetails = serializers.DictField(required=False)


class YieldPredictionSerializer(serializers.Serializer):
    farm_uuid = serializers.CharField(required=False, allow_blank=True)
    plant_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    predictedYieldTons = serializers.FloatField(required=False)
    predictedYieldRaw = serializers.FloatField(required=False)
    unit = serializers.CharField(required=False, allow_blank=True)
    sourceUnit = serializers.CharField(required=False, allow_blank=True)
    simulationEngine = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    simulationModel = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    scenarioId = serializers.IntegerField(required=False)
    simulationWarning = serializers.CharField(required=False, allow_blank=True)
    supportingMetrics = serializers.DictField(required=False)
