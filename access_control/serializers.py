from rest_framework import serializers

from .models import FarmAccessProfile, SubscriptionPlan


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ["uuid", "code", "name", "description", "metadata", "is_active"]


class FarmAccessProfileSerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField()
    subscription_plan = SubscriptionPlanSerializer(allow_null=True)
    features = serializers.DictField()
    groups = serializers.DictField()
    matched_rules = serializers.ListField()
    resolved_from_profile = serializers.BooleanField()


class FarmAccessProfileCacheSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmAccessProfile
        fields = [
            "farm",
            "cached_features",
            "cached_groups",
            "matched_rules",
            "metadata",
            "last_resolved_at",
            "created_at",
            "updated_at",
        ]

