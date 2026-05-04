from rest_framework import serializers

from farm_hub.models import Product


class PlantSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "metadata",
            "light",
            "watering",
            "soil",
            "temperature",
            "growth_stage",
            "growth_stages",
            "icon",
            "planting_season",
            "harvest_time",
            "spacing",
            "fertilizer",
            "health_profile",
            "irrigation_profile",
            "growth_profile",
            "created_at",
            "updated_at",
        ]


class PlantNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["name", "icon", "growth_stages"]
