from rest_framework import serializers


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
