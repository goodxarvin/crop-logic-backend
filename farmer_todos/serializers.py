from rest_framework import serializers

from farmer_calendar.enums import FARMER_TAG_VALUES, PRIORITY_INPUT_MAP
from farmer_calendar.models import FarmerCalendarZone

from .models import FarmerTodoTask


class FarmerTodoTaskResponseSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="uuid", read_only=True)
    zone = serializers.CharField(source="zone.value", read_only=True, allow_null=True)
    scheduledDate = serializers.DateField(source="scheduled_date", format="%Y-%m-%d", read_only=True)
    time = serializers.TimeField(format="%H:%M", read_only=True)
    note = serializers.CharField(source="description", read_only=True)
    tags = serializers.SerializerMethodField()

    class Meta:
        model = FarmerTodoTask
        fields = [
            "id",
            "title",
            "zone",
            "scheduledDate",
            "time",
            "priority",
            "note",
            "tags",
            "status",
        ]

    def get_tags(self, obj):
        raw_tags = obj.extended_props.get("tags", [])
        return [tag for tag in raw_tags if tag in FARMER_TAG_VALUES]


class FarmerTodoChoiceSerializer(serializers.Serializer):
    id = serializers.CharField()
    label = serializers.CharField()
    value = serializers.CharField()


class FarmerTodoZoneSerializer(FarmerTodoChoiceSerializer):
    prefix = "zone_"


class FarmerTodoTagSerializer(FarmerTodoChoiceSerializer):
    pass


class FarmerTodoTaskWriteSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=False)
    zone = serializers.CharField(max_length=255, required=False)
    scheduledDate = serializers.DateField(required=False, format="%Y-%m-%d", input_formats=["%Y-%m-%d"])
    time = serializers.TimeField(required=False, format="%H:%M", input_formats=["%H:%M"])
    priority = serializers.CharField(required=False)
    note = serializers.CharField(required=False, allow_blank=True, default="")
    tags = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        default=list,
        allow_empty=True,
    )
    status = serializers.ChoiceField(choices=[FarmerTodoTask.STATUS_OPEN, FarmerTodoTask.STATUS_DONE], required=False)
    farm_uuid = serializers.UUIDField(required=False, write_only=True)

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("title cannot be empty")
        return value

    def validate_zone(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("zone cannot be empty")
        return value

    def validate_priority(self, value):
        normalized = PRIORITY_INPUT_MAP.get(value.strip().lower(), PRIORITY_INPUT_MAP.get(value.strip()))
        if normalized is None:
            raise serializers.ValidationError("priority must be one of زیاد, متوسط, کم, high, medium, low")
        return normalized

    def validate_tags(self, value):
        normalized = []
        for tag in value:
            cleaned = tag.strip()
            if cleaned:
                if cleaned not in FARMER_TAG_VALUES:
                    raise serializers.ValidationError(f"tag `{cleaned}` is not valid")
                normalized.append(cleaned)
        return normalized

    def validate(self, attrs):
        if not self.partial:
            required_fields = ["title", "zone", "scheduledDate", "time", "priority"]
            errors = {}
            for field in required_fields:
                if field not in attrs:
                    errors[field] = [f"{field} is required"]
            if errors:
                raise serializers.ValidationError(errors)
        return attrs

    @staticmethod
    def _sync_zone(task, zone_value):
        zone, _ = FarmerCalendarZone.objects.get_or_create(
            farm=task.farm,
            value=zone_value,
            defaults={"label": zone_value},
        )
        if zone.label != zone_value:
            zone.label = zone_value
            zone.save(update_fields=["label", "updated_at"])
        task.zone = zone

    def create(self, validated_data):
        zone_value = validated_data.pop("zone")
        tags = validated_data.pop("tags", [])
        validated_data.pop("farm_uuid", None)
        validated_data["scheduled_date"] = validated_data.pop("scheduledDate")
        validated_data["description"] = validated_data.pop("note", "")
        validated_data["extended_props"] = {"tags": tags}
        farm = validated_data["farm"]
        zone, _ = FarmerCalendarZone.objects.get_or_create(
            farm=farm,
            value=zone_value,
            defaults={"label": zone_value},
        )
        if zone.label != zone_value:
            zone.label = zone_value
            zone.save(update_fields=["label", "updated_at"])
        task = FarmerTodoTask.objects.create(zone=zone, **validated_data)
        return task

    def update(self, instance, validated_data):
        zone_value = validated_data.pop("zone", None)
        tags = validated_data.pop("tags", None)
        validated_data.pop("farm_uuid", None)
        if "scheduledDate" in validated_data:
            validated_data["scheduled_date"] = validated_data.pop("scheduledDate")
        if "note" in validated_data:
            validated_data["description"] = validated_data.pop("note")
        if tags is not None:
            extended_props = dict(instance.extended_props or {})
            extended_props["tags"] = tags
            validated_data["extended_props"] = extended_props

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if zone_value is not None:
            self._sync_zone(instance, zone_value)
        instance.save()
        return instance


class FarmerTodoListQuerySerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[FarmerTodoTask.STATUS_OPEN, FarmerTodoTask.STATUS_DONE], required=False)
    priority = serializers.CharField(required=False)
    date = serializers.DateField(required=False, input_formats=["%Y-%m-%d"])
    from_date = serializers.DateField(required=False, input_formats=["%Y-%m-%d"], source="from")
    to = serializers.DateField(required=False, input_formats=["%Y-%m-%d"])
    zone = serializers.CharField(required=False)
    search = serializers.CharField(required=False)
    farm_uuid = serializers.UUIDField(required=False)

    def validate_priority(self, value):
        normalized = PRIORITY_INPUT_MAP.get(value.strip().lower(), PRIORITY_INPUT_MAP.get(value.strip()))
        if normalized is None:
            raise serializers.ValidationError("priority must be one of زیاد, متوسط, کم, high, medium, low")
        return normalized

    def validate(self, attrs):
        from_date = attrs.get("from")
        to_date = attrs.get("to")
        if from_date and to_date and to_date < from_date:
            raise serializers.ValidationError({"to": "to cannot be before from"})
        return attrs
