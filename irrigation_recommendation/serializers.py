from rest_framework import serializers


class IrrigationFarmDataSerializer(serializers.Serializer):
    soilType = serializers.CharField(required=False, allow_blank=True)
    waterQuality = serializers.CharField(required=False, allow_blank=True)
    climateZone = serializers.CharField(required=False, allow_blank=True)


class IrrigationRecommendRequestSerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField(required=True, help_text="UUID مزرعه برای دریافت توصیه آبیاری.")
    plant_name = serializers.CharField(required=False, allow_blank=True, help_text="نام محصول یا گیاه.")
    growth_stage = serializers.CharField(required=False, allow_blank=True, help_text="مرحله رشد گیاه.")
    irrigation_method_name = serializers.CharField(required=False, allow_blank=True, help_text="نام روش آبیاری انتخابی.")


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


class IrrigationRecommendResponseDataSerializer(serializers.Serializer):
    sections = serializers.ListField(child=serializers.DictField(), read_only=True)
