from rest_framework import serializers


class WeatherFarmCardRequestSerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField(
        required=True,
        initial="11111111-1111-1111-1111-111111111111",
        help_text="UUID مزرعه.",
    )


class WeatherChartDataSerializer(serializers.Serializer):
    labels = serializers.ListField(child=serializers.CharField(), required=False)
    series = serializers.ListField(
        child=serializers.ListField(child=serializers.FloatField()),
        required=False,
    )


class FarmWeatherCardSerializer(serializers.Serializer):
    condition = serializers.CharField(required=False, allow_blank=True, help_text="وضعیت فعلی آب‌وهوا.")
    temperature = serializers.FloatField(required=False, help_text="دمای فعلی.")
    unit = serializers.CharField(required=False, allow_blank=True, help_text="واحد دما.")
    humidity = serializers.IntegerField(required=False, help_text="رطوبت نسبی.")
    windSpeed = serializers.FloatField(required=False, help_text="سرعت باد.")
    windUnit = serializers.CharField(required=False, allow_blank=True, help_text="واحد سرعت باد.")
    chartData = WeatherChartDataSerializer(required=False)


class WaterNeedSeriesSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True)
    data = serializers.ListField(child=serializers.FloatField(), required=False)


class WaterNeedPredictionSerializer(serializers.Serializer):
    farm_uuid = serializers.CharField(required=False, allow_blank=True, help_text="UUID مزرعه.")
    totalNext7Days = serializers.FloatField(required=False, help_text="جمع نیاز آبی ۷ روز آینده.")
    unit = serializers.CharField(required=False, allow_blank=True, help_text="واحد نیاز آبی.")
    categories = serializers.ListField(child=serializers.CharField(), required=False, help_text="برچسب روزها یا تاریخ‌ها.")
    series = WaterNeedSeriesSerializer(many=True, required=False)
    dailyBreakdown = serializers.ListField(child=serializers.DictField(), required=False, help_text="جزئیات روزانه پیش‌بینی.")
    insight = serializers.DictField(required=False, help_text="جمع‌بندی و insight تحلیلی.")
    knowledge_base = serializers.CharField(required=False, allow_blank=True, help_text="مرجع دانشی در صورت ارائه توسط upstream.")
    raw_response = serializers.CharField(required=False, allow_blank=True, help_text="پاسخ خام upstream در صورت وجود.")


class WaterStressIndexSerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField(required=False, allow_null=True, help_text="UUID مزرعه.")
    waterStressIndex = serializers.IntegerField(required=False, help_text="شاخص تنش آبی.")
    level = serializers.CharField(required=False, allow_blank=True, help_text="سطح تنش آبی.")
    sourceMetric = serializers.DictField(required=False, help_text="متریک یا منبع محاسبه تنش آبی.")


class WaterSummarySerializer(serializers.Serializer):
    farmWeatherCard = FarmWeatherCardSerializer(required=False)
    waterNeedPrediction = WaterNeedPredictionSerializer(required=False)
    waterStressIndex = WaterStressIndexSerializer(required=False)
