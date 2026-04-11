from rest_framework import serializers

from soil.serializers import (
    SoilAnomalyDetectionSerializer,
    SoilComparisonChartSerializer,
    SoilKpiSerializer,
    SoilMoistureHeatmapSerializer,
    SoilRadarChartSerializer,
)


class Sensor7In1MetaSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True)
    physicalDeviceUuid = serializers.CharField(required=False, allow_null=True)
    sensorCatalogCode = serializers.CharField(required=False, allow_blank=True)
    updatedAt = serializers.CharField(required=False, allow_null=True)


class Sensor7In1ValueSerializer(serializers.Serializer):
    id = serializers.CharField(required=False, allow_blank=True)
    title = serializers.CharField(required=False, allow_blank=True)
    subtitle = serializers.CharField(required=False, allow_blank=True)
    trendNumber = serializers.FloatField(required=False)
    trend = serializers.CharField(required=False, allow_blank=True)
    unit = serializers.CharField(required=False, allow_blank=True)


class Sensor7In1ValuesListSerializer(serializers.Serializer):
    sensor = Sensor7In1MetaSerializer(required=False)
    sensors = Sensor7In1ValueSerializer(many=True, required=False)


class Sensor7In1SummarySerializer(serializers.Serializer):
    sensor = Sensor7In1MetaSerializer(required=False)
    sensorValuesList = Sensor7In1ValuesListSerializer(required=False)
    avgSoilMoisture = SoilKpiSerializer(required=False)
    sensorRadarChart = SoilRadarChartSerializer(required=False)
    sensorComparisonChart = SoilComparisonChartSerializer(required=False)
    anomalyDetectionCard = SoilAnomalyDetectionSerializer(required=False)
    soilMoistureHeatmap = SoilMoistureHeatmapSerializer(required=False)

