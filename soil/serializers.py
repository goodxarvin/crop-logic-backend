from rest_framework import serializers


class SoilKpiSerializer(serializers.Serializer):
    id = serializers.CharField(required=False, allow_blank=True, help_text="شناسه کارت KPI.")
    title = serializers.CharField(required=False, allow_blank=True, help_text="عنوان کارت KPI.")
    subtitle = serializers.CharField(required=False, allow_blank=True, help_text="زیرعنوان کارت KPI.")
    stats = serializers.CharField(required=False, allow_blank=True, help_text="مقدار اصلی KPI.")
    avatarColor = serializers.CharField(required=False, allow_blank=True, help_text="رنگ آواتار کارت.")
    avatarIcon = serializers.CharField(required=False, allow_blank=True, help_text="آیکون کارت.")
    chipText = serializers.CharField(required=False, allow_blank=True, help_text="متن وضعیت KPI.")
    chipColor = serializers.CharField(required=False, allow_blank=True, help_text="رنگ وضعیت KPI.")


class SoilRadarSeriesSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True)
    data = serializers.ListField(child=serializers.FloatField(), required=False)


class SoilRadarChartSerializer(serializers.Serializer):
    labels = serializers.ListField(child=serializers.CharField(), required=False)
    series = SoilRadarSeriesSerializer(many=True, required=False)


class SoilComparisonChartSerializer(serializers.Serializer):
    currentValue = serializers.FloatField(required=False)
    vsLastWeek = serializers.CharField(required=False, allow_blank=True)
    vsLastWeekValue = serializers.FloatField(required=False)
    categories = serializers.ListField(child=serializers.CharField(), required=False)
    series = SoilRadarSeriesSerializer(many=True, required=False)


class SoilAnomalyItemSerializer(serializers.Serializer):
    sensor = serializers.CharField(required=False, allow_blank=True)
    value = serializers.CharField(required=False, allow_blank=True)
    expected = serializers.CharField(required=False, allow_blank=True)
    deviation = serializers.CharField(required=False, allow_blank=True)
    severity = serializers.CharField(required=False, allow_blank=True)


class SoilAnomalyDetectionSerializer(serializers.Serializer):
    farm_uuid = serializers.CharField(required=False, allow_blank=True, help_text="UUID مزرعه.")
    summary = serializers.CharField(required=False, allow_blank=True, help_text="خلاصه کوتاه ناهنجاری خاک.")
    explanation = serializers.CharField(required=False, allow_blank=True, help_text="توضیح کوتاه درباره ناهنجاری.")
    likely_cause = serializers.CharField(required=False, allow_blank=True, help_text="علت محتمل ناهنجاری.")
    recommended_action = serializers.CharField(required=False, allow_blank=True, help_text="اقدام پیشنهادی برای رفع مشکل.")
    monitoring_priority = serializers.CharField(required=False, allow_blank=True, help_text="اولویت پایش؛ low/medium/high/urgent.")
    confidence = serializers.FloatField(required=False, help_text="میزان اطمینان مدل به تحلیل.")
    generated_at = serializers.CharField(required=False, allow_blank=True, help_text="زمان تولید تحلیل.")
    anomalies = SoilAnomalyItemSerializer(many=True, required=False)
    interpretation = serializers.DictField(required=False, help_text="تفسیر ساختاریافته ناهنجاری‌ها.")
    knowledge_base = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text="مرجع دانشی استفاده‌شده.")
    raw_response = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text="پاسخ خام upstream در صورت وجود.")


class SoilHeatmapPointSerializer(serializers.Serializer):
    x = serializers.CharField(required=False, allow_blank=True)
    y = serializers.FloatField(required=False)


class SoilHeatmapSeriesSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True)
    data = SoilHeatmapPointSerializer(many=True, required=False)


class SoilGenericDictSerializer(serializers.Serializer):
    class Meta:
        ref_name = "SoilGenericDict"


class SoilMoistureHeatmapSerializer(serializers.Serializer):
    farm_uuid = serializers.CharField(required=False, allow_blank=True, help_text="UUID مزرعه.")
    location = serializers.DictField(required=False, help_text="اطلاعات مکانی مزرعه یا ناحیه تحلیل.")
    current_sensor = serializers.DictField(required=False, help_text="مشخصات سنسور فعال فعلی.")
    soil_profile = serializers.ListField(child=serializers.DictField(), required=False, help_text="پروفایل خاک در لایه‌های مختلف.")
    timestamp = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text="زمان تولید heatmap.")
    grid_resolution = serializers.DictField(required=False, help_text="رزولوشن شبکه heatmap.")
    grid_cells = serializers.ListField(child=serializers.DictField(), required=False, help_text="سلول‌های شبکه heatmap.")
    sensor_points = serializers.ListField(child=serializers.DictField(), required=False, help_text="نقاط سنسور مؤثر در heatmap.")
    quality_legend = serializers.DictField(required=False, help_text="legend یا بازه‌بندی کیفیت رطوبت.")
    depth_layers = serializers.ListField(child=serializers.DictField(), required=False, help_text="لایه‌های عمقی خاک.")
    model_metadata = serializers.DictField(required=False, help_text="متادیتای مدل تولیدکننده heatmap.")
    summary = serializers.DictField(required=False, help_text="خلاصه تفسیری heatmap.")


class SoilSummarySerializer(serializers.Serializer):
    farm_uuid = serializers.CharField(required=False, allow_blank=True, help_text="UUID مزرعه.")
    healthScore = serializers.IntegerField(required=False, help_text="امتیاز سلامت کلی خاک.")
    profileSource = serializers.CharField(required=False, allow_blank=True, help_text="منبع پروفایل مرجع یا محصول هدف.")
    healthScoreDetails = serializers.DictField(required=False, help_text="جزئیات تشکیل‌دهنده health score.")
    healthLanguage = serializers.DictField(required=False, help_text="توضیحات متنی قابل نمایش برای سلامت خاک.")
    avgSoilMoisture = serializers.IntegerField(required=False, help_text="میانگین رطوبت خاک به‌صورت عدد گرد شده.")
    avgSoilMoistureRaw = serializers.FloatField(required=False, help_text="میانگین خام رطوبت خاک.")
    avgSoilMoistureStatus = serializers.CharField(required=False, allow_blank=True, help_text="وضعیت متنی رطوبت خاک.")
