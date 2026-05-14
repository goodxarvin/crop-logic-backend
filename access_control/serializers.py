from rest_framework import serializers

class FeatureAuthorizationRequestSerializer(serializers.Serializer):
    features = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False,
    )
    action = serializers.CharField(required=False, allow_blank=False, default="view")
