from rest_framework import serializers

from .mock_data import VALID_CARD_IDS, VALID_ROW_IDS


class FarmDashboardConfigSerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField(read_only=True)
    disabled_card_ids = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True,
    )
    row_order = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False,
    )
    enable_drag_reorder = serializers.BooleanField()

    def validate_disabled_card_ids(self, value):
        invalid_ids = [card_id for card_id in value if card_id not in VALID_CARD_IDS]
        if invalid_ids:
            raise serializers.ValidationError(
                f"Invalid card IDs: {', '.join(invalid_ids)}."
            )
        if len(set(value)) != len(value):
            raise serializers.ValidationError("disabled_card_ids must not contain duplicates.")
        return value

    def validate_row_order(self, value):
        invalid_ids = [row_id for row_id in value if row_id not in VALID_ROW_IDS]
        if invalid_ids:
            raise serializers.ValidationError(
                f"Invalid row IDs: {', '.join(invalid_ids)}."
            )
        if len(set(value)) != len(value):
            raise serializers.ValidationError("row_order must not contain duplicates.")
        if set(value) != set(VALID_ROW_IDS):
            raise serializers.ValidationError(
                "row_order must contain each valid row ID exactly once."
            )
        return value


class FarmDashboardConfigPatchSerializer(FarmDashboardConfigSerializer):
    farm_uuid = serializers.UUIDField(required=True)
    disabled_card_ids = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True,
        required=False,
    )
    row_order = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False,
        required=False,
    )
    enable_drag_reorder = serializers.BooleanField(required=False)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if set(attrs.keys()) == {"farm_uuid"}:
            raise serializers.ValidationError("At least one config field must be provided.")
        return attrs
