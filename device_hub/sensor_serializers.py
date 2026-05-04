from rest_framework import serializers

from soil.serializers import SoilAnomalyDetectionSerializer, SoilComparisonChartSerializer, SoilKpiSerializer, SoilMoistureHeatmapSerializer, SoilRadarChartSerializer


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


class SensorComparisonChartQuerySerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField()
    range = serializers.ChoiceField(choices=["7d", "30d"], required=False, default="7d")


class SensorValuesListQuerySerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField()
    range = serializers.ChoiceField(choices=["1h", "24h", "7d"], required=False, default="7d")


class SensorRadarChartQuerySerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField()
    range = serializers.ChoiceField(choices=["today", "7d", "30d"], required=False, default="7d")


class SensorComparisonChartSeriesSerializer(serializers.Serializer):
    name = serializers.CharField()
    data = serializers.ListField(child=serializers.FloatField())


class SensorComparisonChartResponseSerializer(serializers.Serializer):
    series = SensorComparisonChartSeriesSerializer(many=True)
    categories = serializers.ListField(child=serializers.CharField())
    currentValue = serializers.FloatField()
    vsLastWeek = serializers.CharField()


class SensorValuesListItemSerializer(serializers.Serializer):
    title = serializers.CharField()
    subtitle = serializers.CharField()
    trendNumber = serializers.FloatField()
    trend = serializers.ChoiceField(choices=["positive", "negative"])
    unit = serializers.CharField()


class SensorValuesListResponseSerializer(serializers.Serializer):
    sensors = SensorValuesListItemSerializer(many=True)


class SensorRadarChartResponseSerializer(serializers.Serializer):
    labels = serializers.ListField(child=serializers.CharField())
    series = SensorComparisonChartSeriesSerializer(many=True)


class Sensor7In1SummarySerializer(serializers.Serializer):
    sensor = Sensor7In1MetaSerializer(required=False)
    sensorValuesList = Sensor7In1ValuesListSerializer(required=False)
    avgSoilMoisture = SoilKpiSerializer(required=False)
    sensorRadarChart = SoilRadarChartSerializer(required=False)
    sensorComparisonChart = SoilComparisonChartSerializer(required=False)
    anomalyDetectionCard = SoilAnomalyDetectionSerializer(required=False)
    soilMoistureHeatmap = SoilMoistureHeatmapSerializer(required=False)


class DeviceMetaSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True)
    physicalDeviceUuid = serializers.CharField(required=False, allow_null=True)
    sensorCatalogCode = serializers.CharField(required=False, allow_blank=True)
    updatedAt = serializers.CharField(required=False, allow_null=True)


class DeviceFieldValueSerializer(serializers.Serializer):
    id = serializers.CharField(required=False, allow_blank=True)
    title = serializers.CharField(required=False, allow_blank=True)
    subtitle = serializers.CharField(required=False, allow_blank=True)
    trendNumber = serializers.FloatField(required=False)
    trend = serializers.CharField(required=False, allow_blank=True)
    unit = serializers.CharField(required=False, allow_blank=True)


class DeviceValuesListSerializer(serializers.Serializer):
    sensor = DeviceMetaSerializer(required=False)
    sensors = DeviceFieldValueSerializer(many=True, required=False)


class DeviceSummarySerializer(serializers.Serializer):
    sensor = DeviceMetaSerializer(required=False)
    supportedWidgets = serializers.ListField(child=serializers.CharField(), required=False)
    sensorValuesList = DeviceValuesListSerializer(required=False)
    avgSoilMoisture = SoilKpiSerializer(required=False)
    sensorRadarChart = SoilRadarChartSerializer(required=False)
    sensorComparisonChart = SoilComparisonChartSerializer(required=False)
    anomalyDetectionCard = SoilAnomalyDetectionSerializer(required=False)
    soilMoistureHeatmap = SoilMoistureHeatmapSerializer(required=False)
    commands = serializers.ListField(child=serializers.JSONField(), required=False)
