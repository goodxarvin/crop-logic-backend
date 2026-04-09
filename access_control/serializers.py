from rest_framework import serializers

from .models import SubscriptionPlan


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ["uuid", "code", "name"]


class FeatureAuthorizationRequestSerializer(serializers.Serializer):
    features = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False,
    )
    action = serializers.CharField(required=False, allow_blank=False, default="view")
