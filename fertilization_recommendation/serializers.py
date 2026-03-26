from rest_framework import serializers


class FertilizationFarmDataSerializer(serializers.Serializer):
    soilType = serializers.CharField(required=False, allow_blank=True)
    organicMatter = serializers.CharField(required=False, allow_blank=True)
    waterEC = serializers.CharField(required=False, allow_blank=True)


class FertilizationRecommendRequestSerializer(serializers.Serializer):
    crop_id = serializers.CharField(required=False, allow_blank=True)
    growth_stage = serializers.CharField(required=False, allow_blank=True)
    farm_data = FertilizationFarmDataSerializer(required=False)
    soilType = serializers.CharField(required=False, allow_blank=True)
    organicMatter = serializers.CharField(required=False, allow_blank=True)
    waterEC = serializers.CharField(required=False, allow_blank=True)


class FertilizationPlanSerializer(serializers.Serializer):
    npkRatio = serializers.CharField(required=False, allow_blank=True)
    amountPerHectare = serializers.CharField(required=False, allow_blank=True)
    applicationMethod = serializers.CharField(required=False, allow_blank=True)
    applicationInterval = serializers.CharField(required=False, allow_blank=True)
    reasoning = serializers.CharField(required=False, allow_blank=True)


class FertilizationRecommendResponseDataSerializer(serializers.Serializer):
    plan = FertilizationPlanSerializer(required=False)


class FertilizationTaskSubmitDataSerializer(serializers.Serializer):
    task_id = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False, allow_blank=True)


class FertilizationTaskProgressSerializer(serializers.Serializer):
    message = serializers.CharField(required=False, allow_blank=True)


class FertilizationTaskStatusDataSerializer(serializers.Serializer):
    task_id = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False, allow_blank=True)
    progress = FertilizationTaskProgressSerializer(required=False)
    result = FertilizationRecommendResponseDataSerializer(required=False)
