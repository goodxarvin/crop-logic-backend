from rest_framework import serializers


class WeatherChartDataSerializer(serializers.Serializer):
    labels = serializers.ListField(child=serializers.CharField(), required=False)
    series = serializers.ListField(
        child=serializers.ListField(child=serializers.FloatField()),
        required=False,
    )


class FarmWeatherCardSerializer(serializers.Serializer):
    condition = serializers.CharField(required=False, allow_blank=True)
    temperature = serializers.FloatField(required=False)
    unit = serializers.CharField(required=False, allow_blank=True)
    humidity = serializers.IntegerField(required=False)
    windSpeed = serializers.FloatField(required=False)
    windUnit = serializers.CharField(required=False, allow_blank=True)
    chartData = WeatherChartDataSerializer(required=False)


class WaterNeedSeriesSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True)
    data = serializers.ListField(child=serializers.FloatField(), required=False)


class WaterNeedPredictionSerializer(serializers.Serializer):
    totalNext7Days = serializers.FloatField(required=False)
    unit = serializers.CharField(required=False, allow_blank=True)
    categories = serializers.ListField(child=serializers.CharField(), required=False)
    series = WaterNeedSeriesSerializer(many=True, required=False)


class WaterStressIndexSerializer(serializers.Serializer):
    id = serializers.CharField(required=False, allow_blank=True)
    title = serializers.CharField(required=False, allow_blank=True)
    subtitle = serializers.CharField(required=False, allow_blank=True)
    stats = serializers.CharField(required=False, allow_blank=True)
    avatarColor = serializers.CharField(required=False, allow_blank=True)
    avatarIcon = serializers.CharField(required=False, allow_blank=True)
    chipText = serializers.CharField(required=False, allow_blank=True)
    chipColor = serializers.CharField(required=False, allow_blank=True)


class WaterSummarySerializer(serializers.Serializer):
    farmWeatherCard = FarmWeatherCardSerializer(required=False)
    waterNeedPrediction = WaterNeedPredictionSerializer(required=False)
    waterStressIndex = WaterStressIndexSerializer(required=False)
