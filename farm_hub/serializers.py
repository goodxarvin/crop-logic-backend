from rest_framework import serializers

from .models import FarmHub, FarmSensor, FarmType, Product


class FarmTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmType
        fields = ["uuid", "name", "description", "metadata"]


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["uuid", "name", "description", "metadata"]


class FarmSensorSerializer(serializers.ModelSerializer):
    last_updated = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = FarmSensor
        fields = [
            "uuid",
            "name",
            "sensor_type",
            "is_active",
            "specifications",
            "power_source",
            "customization",
            "last_updated",
        ]
        read_only_fields = ["uuid", "last_updated"]


class FarmHubSerializer(serializers.ModelSerializer):
    last_updated = serializers.DateTimeField(source="updated_at", read_only=True)
    farm_type = FarmTypeSerializer(read_only=True)
    products = ProductSerializer(many=True, read_only=True)
    sensors = FarmSensorSerializer(many=True, read_only=True)

    class Meta:
        model = FarmHub
        fields = [
            "farm_uuid",
            "name",
            "is_active",
            "customization",
            "farm_type",
            "products",
            "sensors",
            "last_updated",
        ]
        read_only_fields = ["farm_uuid", "last_updated"]


class FarmSensorWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmSensor
        fields = [
            "name",
            "sensor_type",
            "is_active",
            "specifications",
            "power_source",
            "customization",
        ]


class FarmHubCreateSerializer(serializers.ModelSerializer):
    area_geojson = serializers.JSONField(write_only=True, required=False)
    farm_type_uuid = serializers.UUIDField(write_only=True)
    product_uuids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        allow_empty=False,
    )
    sensors = FarmSensorWriteSerializer(many=True, required=False)

    class Meta:
        model = FarmHub
        fields = [
            "name",
            "is_active",
            "customization",
            "farm_type_uuid",
            "product_uuids",
            "sensors",
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

    def validate(self, attrs):
        farm_type_uuid = attrs.get("farm_type_uuid")
        product_uuids = attrs.get("product_uuids")

        if farm_type_uuid is None:
            if self.instance is None:
                raise serializers.ValidationError({"farm_type_uuid": ["This field is required."]})
            farm_type = self.instance.farm_type
        else:
            try:
                farm_type = FarmType.objects.get(uuid=farm_type_uuid)
            except FarmType.DoesNotExist as exc:
                raise serializers.ValidationError({"farm_type_uuid": ["Farm type not found."]}) from exc

        if product_uuids is None:
            products = list(self.instance.products.all()) if self.instance is not None else []
        else:
            products = list(Product.objects.filter(uuid__in=product_uuids))
            if len(products) != len(product_uuids):
                raise serializers.ValidationError({"product_uuids": ["One or more products were not found."]})

        invalid_products = [product.name for product in products if product.farm_type_id != farm_type.id]
        if invalid_products:
            raise serializers.ValidationError(
                {"product_uuids": [f"Products must belong to farm type `{farm_type.name}`."]}
            )

        attrs["farm_type"] = farm_type
        attrs["products"] = products
        return attrs

    def create(self, validated_data):
        validated_data.pop("area_geojson", None)
        sensors_data = validated_data.pop("sensors", [])
        products = validated_data.pop("products", [])
        validated_data["farm_type"] = validated_data.pop("farm_type")
        validated_data.pop("farm_type_uuid", None)
        validated_data.pop("product_uuids", None)

        farm = super().create(validated_data)
        if products:
            farm.products.set(products)
        if sensors_data:
            FarmSensor.objects.bulk_create([FarmSensor(farm=farm, **sensor_data) for sensor_data in sensors_data])
        return farm

    def update(self, instance, validated_data):
        validated_data.pop("area_geojson", None)
        sensors_data = validated_data.pop("sensors", None)
        products = validated_data.pop("products", None)
        farm_type = validated_data.pop("farm_type", None)
        validated_data.pop("farm_type_uuid", None)
        validated_data.pop("product_uuids", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if farm_type is not None:
            instance.farm_type = farm_type
        instance.save()

        if products is not None:
            instance.products.set(products)
        if sensors_data is not None:
            instance.sensors.all().delete()
            if sensors_data:
                FarmSensor.objects.bulk_create([FarmSensor(farm=instance, **sensor_data) for sensor_data in sensors_data])

        return instance


class FarmToggleSerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField()
