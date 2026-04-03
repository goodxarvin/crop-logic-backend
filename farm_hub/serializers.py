from rest_framework import serializers
from access_control.models import SubscriptionPlan
from access_control.serializers import SubscriptionPlanSerializer
from access_control.catalog import GOLD_PLAN_CODE
from access_control.services import get_effective_subscription_plan

from .models import FarmHub, FarmSensor, FarmType, Product
from sensor_catalog.models import SensorCatalog


class FarmTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmType
        fields = ["uuid", "name", "description", "metadata"]


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "uuid",
            "name",
            "description",
            "metadata",
            "light",
            "watering",
            "soil",
            "temperature",
            "planting_season",
            "harvest_time",
            "spacing",
            "fertilizer",
            "health_profile",
            "irrigation_profile",
            "growth_profile",
        ]


class FarmSensorSerializer(serializers.ModelSerializer):
    last_updated = serializers.DateTimeField(source="updated_at", read_only=True)
    sensor_catalog_uuid = serializers.UUIDField(source="sensor_catalog.uuid", read_only=True)

    class Meta:
        model = FarmSensor
        fields = [
            "uuid",
            "sensor_catalog_uuid",
            "physical_device_uuid",
            "name",
            "sensor_type",
            "is_active",
            "specifications",
            "power_source",
            "last_updated",
        ]
        read_only_fields = ["uuid", "last_updated"]


class FarmHubSerializer(serializers.ModelSerializer):
    last_updated = serializers.DateTimeField(source="updated_at", read_only=True)
    farm_type = FarmTypeSerializer(read_only=True)
    subscription_plan = serializers.SerializerMethodField()
    products = ProductSerializer(many=True, read_only=True)
    sensors = FarmSensorSerializer(many=True, read_only=True)
    area_uuid = serializers.UUIDField(source="current_crop_area.uuid", read_only=True)

    class Meta:
        model = FarmHub
        fields = [
            "farm_uuid",
            "area_uuid",
            "name",
            "is_active",
            "farm_type",
            "subscription_plan",
            "products",
            "sensors",
            "last_updated",
        ]
        read_only_fields = ["farm_uuid", "last_updated"]

    def get_subscription_plan(self, obj):
        subscription_plan = get_effective_subscription_plan(obj)
        if subscription_plan is None:
            return None
        return SubscriptionPlanSerializer(subscription_plan, context=self.context).data


class FarmSensorWriteSerializer(serializers.ModelSerializer):
    sensor_catalog_uuid = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = FarmSensor
        fields = [
            "sensor_catalog_uuid",
            "physical_device_uuid",
            "name",
            "sensor_type",
            "is_active",
            "specifications",
            "power_source",
        ]

    def validate(self, attrs):
        sensor_catalog_uuid = attrs.pop("sensor_catalog_uuid", None)
        if sensor_catalog_uuid is not None:
            try:
                sensor_catalog = SensorCatalog.objects.get(uuid=sensor_catalog_uuid)
            except SensorCatalog.DoesNotExist as exc:
                raise serializers.ValidationError({"sensor_catalog_uuid": ["Sensor catalog not found."]}) from exc
            attrs["sensor_catalog"] = sensor_catalog
            attrs.setdefault("name", sensor_catalog.name)

        return attrs


class FarmHubCreateSerializer(serializers.ModelSerializer):
    area_geojson = serializers.JSONField(write_only=True, required=False)
    farm_type_uuid = serializers.UUIDField(write_only=True)
    subscription_plan_uuid = serializers.UUIDField(write_only=True, required=False, allow_null=True)
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
            "farm_type_uuid",
            "subscription_plan_uuid",
            "product_uuids",
            "sensors",
            "area_geojson",
        ]

    def to_internal_value(self, data):
        if hasattr(data, "copy"):
            data = data.copy()
            data.pop("farm_uuid", None)
        return super().to_internal_value(data)

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
        subscription_plan_uuid = attrs.get("subscription_plan_uuid", serializers.empty)
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

        if subscription_plan_uuid is serializers.empty:
            if self.instance is not None:
                subscription_plan = self.instance.subscription_plan
            else:
                subscription_plan = SubscriptionPlan.objects.filter(code=GOLD_PLAN_CODE, is_active=True).first()
        elif subscription_plan_uuid is None:
            subscription_plan = None
        else:
            try:
                subscription_plan = SubscriptionPlan.objects.get(uuid=subscription_plan_uuid, is_active=True)
            except SubscriptionPlan.DoesNotExist as exc:
                raise serializers.ValidationError({"subscription_plan_uuid": ["Subscription plan not found."]}) from exc

        attrs["farm_type"] = farm_type
        attrs["subscription_plan"] = subscription_plan
        attrs["products"] = products
        return attrs

    def create(self, validated_data):
        validated_data.pop("area_geojson", None)
        sensors_data = validated_data.pop("sensors", [])
        products = validated_data.pop("products", [])
        validated_data["farm_type"] = validated_data.pop("farm_type")
        validated_data["subscription_plan"] = validated_data.pop("subscription_plan", None)
        validated_data.pop("farm_type_uuid", None)
        validated_data.pop("subscription_plan_uuid", None)
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
        subscription_plan = validated_data.pop("subscription_plan", serializers.empty)
        validated_data.pop("farm_type_uuid", None)
        validated_data.pop("subscription_plan_uuid", None)
        validated_data.pop("product_uuids", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if farm_type is not None:
            instance.farm_type = farm_type
        if subscription_plan is not serializers.empty:
            instance.subscription_plan = subscription_plan
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
