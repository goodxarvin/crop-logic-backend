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
    expandableExplanation = serializers.CharField(required=False, allow_blank=True)


class ConversationSummarySerializer(serializers.Serializer):
    id = serializers.UUIDField(source="uuid", read_only=True)
    message_count = serializers.IntegerField(read_only=True)


class ConversationCreateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, allow_blank=True, max_length=255)
    farm_context = serializers.JSONField(required=False)


class ChatHistoryMessageSerializer(serializers.Serializer):
    message_id = serializers.UUIDField(read_only=True)
    conversation_id = serializers.UUIDField(read_only=True)
    role = serializers.ChoiceField(choices=Message.ROLE_CHOICES, read_only=True)
    content = serializers.CharField(read_only=True, allow_blank=True)
    sections = ChatSectionSerializer(many=True, read_only=True)
    images = serializers.ListField(child=serializers.CharField(), read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class ConversationMessagesSerializer(serializers.Serializer):
    conversation_id = serializers.UUIDField(read_only=True)
    messages = ChatHistoryMessageSerializer(many=True, read_only=True)


class ChatResponseDataSerializer(serializers.Serializer):
    message_id = serializers.UUIDField(read_only=True)
    conversation_id = serializers.UUIDField(read_only=True)
    content = serializers.CharField(read_only=True, allow_blank=True)
    sections = ChatSectionSerializer(many=True, read_only=True)


class ConversationDeleteSerializer(serializers.Serializer):
    conversation_id = serializers.UUIDField(read_only=True)


class ChatPostSerializer(serializers.Serializer):
    content = serializers.CharField(required=False, allow_blank=True, default="")
    images = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
    )
    conversation_id = serializers.UUIDField(required=False)
    title = serializers.CharField(required=False, allow_blank=True, max_length=255)
    farm_context = serializers.JSONField(required=False)

    def validate(self, attrs):
        content = attrs.get("content", "").strip()
        images = attrs.get("images") or []
        if not content and not images:
            raise serializers.ValidationError("Either content or images is required.")
        return attrs
