from rest_framework import serializers

from .models import SensorCatalog


class SensorCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorCatalog
        fields = [
            "uuid",
            "code",
            "name",
            "description",
            "customizable_fields",
            "supported_power_sources",
            "returned_data_fields",
            "sample_payload",
            "is_active",
        ]
        read_only_fields = fields
