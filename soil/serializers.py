from rest_framework import serializers


class SoilKpiSerializer(serializers.Serializer):
    id = serializers.CharField(required=False, allow_blank=True)
    title = serializers.CharField(required=False, allow_blank=True)
    subtitle = serializers.CharField(required=False, allow_blank=True)
    stats = serializers.CharField(required=False, allow_blank=True)
    avatarColor = serializers.CharField(required=False, allow_blank=True)
    avatarIcon = serializers.CharField(required=False, allow_blank=True)
    chipText = serializers.CharField(required=False, allow_blank=True)
    chipColor = serializers.CharField(required=False, allow_blank=True)


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
    anomalies = SoilAnomalyItemSerializer(many=True, required=False)


class SoilHeatmapPointSerializer(serializers.Serializer):
    x = serializers.CharField(required=False, allow_blank=True)
    y = serializers.FloatField(required=False)


class SoilHeatmapSeriesSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True)
    data = SoilHeatmapPointSerializer(many=True, required=False)


class SoilMoistureHeatmapSerializer(serializers.Serializer):
    zones = serializers.ListField(child=serializers.CharField(), required=False)
    hours = serializers.ListField(child=serializers.CharField(), required=False)
    series = SoilHeatmapSeriesSerializer(many=True, required=False)


class SoilSummarySerializer(serializers.Serializer):
    avgSoilMoisture = SoilKpiSerializer(required=False)
    sensorRadarChart = SoilRadarChartSerializer(required=False)
    sensorComparisonChart = SoilComparisonChartSerializer(required=False)
    anomalyDetectionCard = SoilAnomalyDetectionSerializer(required=False)
    soilMoistureHeatmap = SoilMoistureHeatmapSerializer(required=False)
