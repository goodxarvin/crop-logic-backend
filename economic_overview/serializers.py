from rest_framework import serializers


class EconomicDataItemSerializer(serializers.Serializer):
    title = serializers.CharField()
    value = serializers.CharField()
    subtitle = serializers.CharField()
    avatarIcon = serializers.CharField()
    avatarColor = serializers.CharField()


class ChartSeriesSerializer(serializers.Serializer):
    name = serializers.CharField()
    data = serializers.ListField(child=serializers.FloatField())


class EconomicOverviewSerializer(serializers.Serializer):
    economicData = EconomicDataItemSerializer(many=True)
    chartSeries = ChartSeriesSerializer(many=True)
    chartCategories = serializers.ListField(child=serializers.CharField())
