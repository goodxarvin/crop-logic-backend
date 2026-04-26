from rest_framework import serializers


class EconomicDataItemSerializer(serializers.Serializer):
    title = serializers.CharField(help_text="عنوان شاخص اقتصادی.")
    value = serializers.CharField(help_text="مقدار شاخص اقتصادی.")
    subtitle = serializers.CharField(help_text="توضیح تکمیلی شاخص.")
    avatarIcon = serializers.CharField(help_text="آیکون نمایشی شاخص.")
    avatarColor = serializers.CharField(help_text="رنگ نمایشی شاخص.")


class ChartSeriesSerializer(serializers.Serializer):
    name = serializers.CharField()
    data = serializers.ListField(child=serializers.FloatField())


class EconomicOverviewSerializer(serializers.Serializer):
    farm_uuid = serializers.CharField(required=False, allow_blank=True, help_text="UUID مزرعه.")
    source = serializers.CharField(required=False, allow_blank=True, help_text="منبع داده یا نوع تولید پاسخ.")
    economicData = EconomicDataItemSerializer(many=True)
    chartSeries = ChartSeriesSerializer(many=True)
    chartCategories = serializers.ListField(child=serializers.CharField(), help_text="برچسب‌های محور افقی نمودار اقتصادی.")


class EconomicOverviewRequestSerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField(required=True, help_text="UUID مزرعه برای دریافت نمای اقتصادی.")
