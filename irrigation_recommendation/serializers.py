from rest_framework import serializers


class IrrigationFarmDataSerializer(serializers.Serializer):
    soilType = serializers.CharField(required=False, allow_blank=True)
    waterQuality = serializers.CharField(required=False, allow_blank=True)
    climateZone = serializers.CharField(required=False, allow_blank=True)


class IrrigationRecommendRequestSerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField(required=True)
    crop_id = serializers.CharField(required=False, allow_blank=True)
    farm_data = IrrigationFarmDataSerializer(required=False)
    soilType = serializers.CharField(required=False, allow_blank=True)
    waterQuality = serializers.CharField(required=False, allow_blank=True)
    climateZone = serializers.CharField(required=False, allow_blank=True)


class IrrigationPlanSerializer(serializers.Serializer):
    frequencyPerWeek = serializers.CharField(required=False, allow_blank=True)
    durationMinutes = serializers.CharField(required=False, allow_blank=True)
    bestTimeOfDay = serializers.CharField(required=False, allow_blank=True)
    moistureLevel = serializers.CharField(required=False, allow_blank=True)
    warning = serializers.CharField(required=False, allow_blank=True)


class IrrigationWaterBalanceDaySerializer(serializers.Serializer):
    forecast_date = serializers.CharField(required=False, allow_blank=True)
    et0_mm = serializers.FloatField(required=False)
    etc_mm = serializers.FloatField(required=False)
    effective_rainfall_mm = serializers.FloatField(required=False)
    gross_irrigation_mm = serializers.FloatField(required=False)
    irrigation_timing = serializers.CharField(required=False, allow_blank=True)


class IrrigationCropProfileSerializer(serializers.Serializer):
    kc_initial = serializers.FloatField(required=False)
    kc_mid = serializers.FloatField(required=False)
    kc_end = serializers.FloatField(required=False)


class IrrigationWaterBalanceSerializer(serializers.Serializer):
    daily = IrrigationWaterBalanceDaySerializer(many=True, required=False)
    crop_profile = IrrigationCropProfileSerializer(required=False)
    active_kc = serializers.FloatField(required=False)


class IrrigationRecommendResponseDataSerializer(serializers.Serializer):
    plan = IrrigationPlanSerializer(required=False)
    raw_response = serializers.CharField(required=False, allow_blank=True)
    water_balance = IrrigationWaterBalanceSerializer(required=False)
    status = serializers.CharField(required=False, allow_blank=True)


class IrrigationTaskSubmitDataSerializer(serializers.Serializer):
    task_id = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False, allow_blank=True)


class IrrigationTaskStatusDataSerializer(serializers.Serializer):
    task_id = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False, allow_blank=True)
    result = IrrigationRecommendResponseDataSerializer(required=False)
