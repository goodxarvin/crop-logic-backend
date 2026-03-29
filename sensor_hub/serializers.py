from rest_framework import serializers


from .models import Sensor


class SensorSerializer(serializers.ModelSerializer):
    last_updated = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = Sensor
        fields = [
            "uuid_sensor",
            "name",
            "is_active",
            "specifications",
            "power_source",
            "customized_sensors",
            "last_updated",
        ]
        read_only_fields = ["uuid_sensor", "last_updated"]


class SensorCreateSerializer(serializers.ModelSerializer):
    area_geojson = serializers.JSONField(write_only=True, required=False)

    class Meta:
        model = Sensor
        fields = [
            "name",
            "specifications",
            "power_source",
            "customized_sensors",
            "area_geojson",
        ]

    def validate_area_geojson(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("`area_geojson` must be a GeoJSON object.")

        geometry = value.get("geometry") if value.get("type") == "Feature" else value
        if not isinstance(geometry, dict):
            raise serializers.ValidationError("`area_geojson.geometry` is required.")

        if geometry.get("type") != "Polygon":
            raise serializers.ValidationError("`area_geojson.geometry.type` must be `Polygon`.")

        coordinates = geometry.get("coordinates")
        if not isinstance(coordinates, list) or not coordinates or not isinstance(coordinates[0], list):
            raise serializers.ValidationError("`area_geojson.geometry.coordinates` must be a polygon ring.")

        return value


class SensorToggleSerializer(serializers.Serializer):
    uuid_sensor = serializers.UUIDField()
