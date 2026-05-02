from rest_framework import serializers

from .enums import FARMER_TAG_ITEMS, FARMER_TAG_VALUES
from .models import FarmerCalendarEvent


class FarmerCalendarEventResponseSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="uuid", read_only=True)
    tags = serializers.SerializerMethodField()
    extendedProps = serializers.SerializerMethodField()

    class Meta:
        model = FarmerCalendarEvent
        fields = [
            "id",
            "title",
            "description",
            "deadline",
            "tags",
            "start",
            "end",
            "extendedProps",
        ]

    def get_tags(self, obj):
        raw_tags = obj.extended_props.get("tags", [])
        return [tag for tag in raw_tags if tag in FARMER_TAG_VALUES]

    def get_extendedProps(self, obj):
        extended_props = dict(obj.extended_props or {})
        extended_props.pop("tags", None)
        return extended_props


class FarmerCalendarEventWriteSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    deadline = serializers.IntegerField(required=False, allow_null=True)
    tags = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        default=list,
        allow_empty=True,
    )
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
    extendedProps = serializers.JSONField(required=False, default=dict)
    farm_uuid = serializers.UUIDField(required=False, write_only=True)

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("title cannot be empty")
        return value

    def validate_tags(self, value):
        normalized = []
        for tag in value:
            cleaned = tag.strip()
            if cleaned:
                if cleaned not in FARMER_TAG_VALUES:
                    raise serializers.ValidationError(f"tag `{cleaned}` is not valid")
                normalized.append(cleaned)
        return normalized

    def validate_extendedProps(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("extendedProps must be an object")
        return value

    def validate(self, attrs):
        if attrs["end"] < attrs["start"]:
            raise serializers.ValidationError({"end": "end cannot be before start"})
        return attrs

    def create(self, validated_data):
        tags = validated_data.pop("tags", [])
        validated_data.pop("farm_uuid", None)
        extended_props = validated_data.pop("extendedProps", {})
        extended_props["tags"] = tags
        validated_data["extended_props"] = extended_props
        event = FarmerCalendarEvent.objects.create(**validated_data)
        return event

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", None)
        validated_data.pop("farm_uuid", None)
        if "extendedProps" in validated_data:
            validated_data["extended_props"] = validated_data.pop("extendedProps")
        if tags is not None:
            extended_props = dict(instance.extended_props or {})
            if "extended_props" in validated_data:
                extended_props.update(validated_data["extended_props"] or {})
            extended_props["tags"] = tags
            validated_data["extended_props"] = extended_props

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class FarmerCalendarListQuerySerializer(serializers.Serializer):
    start = serializers.DateTimeField(required=False)
    end = serializers.DateTimeField(required=False)
    farm_uuid = serializers.UUIDField(required=False)

    def validate(self, attrs):
        start = attrs.get("start")
        end = attrs.get("end")
        if start and end and end < start:
            raise serializers.ValidationError({"end": "end cannot be before start"})
        return attrs


class FarmerCalendarTagIdSerializer(serializers.Serializer):
    id = serializers.CharField()
    label = serializers.CharField()
    value = serializers.CharField()
