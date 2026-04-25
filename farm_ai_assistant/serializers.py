from rest_framework import serializers

from .models import Message


class ChatSectionSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["text", "list", "recommendation", "warning"])
    title = serializers.CharField(required=False, allow_blank=True)
    content = serializers.CharField(required=False, allow_blank=True)
    items = serializers.ListField(child=serializers.CharField(), required=False)
    icon = serializers.CharField(required=False, allow_blank=True)
    frequency = serializers.CharField(required=False, allow_blank=True)
    amount = serializers.CharField(required=False, allow_blank=True)
    timing = serializers.CharField(required=False, allow_blank=True)
    primaryAction = serializers.CharField(required=False, allow_blank=True)
    validityPeriod = serializers.CharField(required=False, allow_blank=True)
    expandableExplanation = serializers.CharField(required=False, allow_blank=True)


class ConversationSummarySerializer(serializers.Serializer):
    id = serializers.UUIDField(source="uuid", read_only=True)
    farm_uuid = serializers.UUIDField(source="farm.farm_uuid", read_only=True, allow_null=True)
    message_count = serializers.IntegerField(read_only=True)


class ConversationCreateSerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField(required=False, allow_null=True)
    title = serializers.CharField(required=False, allow_blank=True, max_length=255)
    farm_context = serializers.JSONField(required=False)


class ChatHistoryMessageSerializer(serializers.Serializer):
    message_id = serializers.UUIDField(read_only=True)
    conversation_id = serializers.UUIDField(read_only=True)
    farm_uuid = serializers.UUIDField(read_only=True, allow_null=True)
    role = serializers.ChoiceField(choices=Message.ROLE_CHOICES, read_only=True)
    content = serializers.CharField(read_only=True, allow_blank=True)
    sections = ChatSectionSerializer(many=True, read_only=True)
    images = serializers.ListField(child=serializers.CharField(), read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class ConversationMessagesSerializer(serializers.Serializer):
    conversation_id = serializers.UUIDField(read_only=True)
    farm_uuid = serializers.UUIDField(read_only=True, allow_null=True)
    messages = ChatHistoryMessageSerializer(many=True, read_only=True)


class ChatResponseDataSerializer(serializers.Serializer):
    message_id = serializers.UUIDField(read_only=True)
    conversation_id = serializers.UUIDField(read_only=True)
    farm_uuid = serializers.UUIDField(read_only=True, allow_null=True)
    content = serializers.CharField(read_only=True, allow_blank=True)
    sections = ChatSectionSerializer(many=True, read_only=True)


class ConversationDeleteSerializer(serializers.Serializer):
    conversation_id = serializers.UUIDField(read_only=True)
    farm_uuid = serializers.UUIDField(read_only=True, allow_null=True)


class ChatPostSerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField(required=True)
    query = serializers.CharField(required=False, allow_blank=True, default="")
    history = serializers.JSONField(required=False)
    image_urls = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
    )
    images = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
    )
    conversation_id = serializers.UUIDField(required=False)

    def validate(self, attrs):
        query = (attrs.get("query") or "").strip()
        image_urls = attrs.get("image_urls") or []
        images = attrs.get("images") or []
        history = attrs.get("history", [])

        if isinstance(history, str):
            try:
                history = serializers.JSONField().to_internal_value(history)
            except serializers.ValidationError as exc:
                raise serializers.ValidationError({"history": exc.detail}) from exc

        if history in (None, ""):
            history = []
        if not isinstance(history, list):
            raise serializers.ValidationError({"history": ["History must be an array or a valid JSON array string."]})

        if not query and not image_urls and not images:
            raise serializers.ValidationError({"query": ["This field may not be blank unless an image is sent."]})

        attrs["query"] = query
        attrs["history"] = history
        return attrs
