from rest_framework import serializers


class CropHealthRequestSerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField(help_text="UUID مزرعه برای دریافت تحلیل سلامت گیاه.")


class HealthDataItemSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, allow_blank=True, help_text="عنوان آیتم سلامت.")
    value = serializers.JSONField(required=False, help_text="مقدار آیتم سلامت؛ می‌تواند عدد، متن یا ساختار JSON باشد.")
    color = serializers.CharField(required=False, allow_blank=True, help_text="رنگ نمایشی آیتم سلامت.")
    icon = serializers.CharField(required=False, allow_blank=True, help_text="آیکون نمایشی آیتم سلامت.")


class NdviHealthCardSerializer(serializers.Serializer):
    ndviIndex = serializers.FloatField(required=False, help_text="شاخص NDVI نرمال‌شده برای مزرعه.")
    mean_ndvi = serializers.FloatField(required=False, help_text="میانگین NDVI محاسبه‌شده.")
    ndvi_map = serializers.JSONField(required=False, help_text="لایه یا متادیتای نقشه NDVI.")
    vegetation_health_class = serializers.CharField(required=False, allow_blank=True, help_text="کلاس سلامت پوشش گیاهی.")
    observation_date = serializers.DateField(required=False, help_text="تاریخ مشاهده ماهواره‌ای.")
    satellite_source = serializers.CharField(required=False, allow_blank=True, help_text="منبع تصویر ماهواره‌ای.")
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
