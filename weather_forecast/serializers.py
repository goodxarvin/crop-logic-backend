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
