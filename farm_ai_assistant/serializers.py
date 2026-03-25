from rest_framework import serializers

from .models import Conversation, Message


class ConversationListSerializer(serializers.ModelSerializer):
    conversation_id = serializers.UUIDField(source="uuid", read_only=True)
    last_message_preview = serializers.SerializerMethodField()
    message_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Conversation
        fields = [
            "conversation_id",
            "title",
            "farm_context",
            "message_count",
            "last_message_preview",
            "created_at",
            "updated_at",
        ]

    def get_last_message_preview(self, obj):
        last_message = getattr(obj, "last_message", None)
        if last_message is None:
            last_message = obj.messages.order_by("-created_at", "-id").first()
        if last_message is None:
            return ""
        return (last_message.content or "")[:120]


class MessageSerializer(serializers.ModelSerializer):
    message_id = serializers.UUIDField(source="uuid", read_only=True)
    conversation_id = serializers.UUIDField(source="conversation.uuid", read_only=True)

    class Meta:
        model = Message
        fields = [
            "message_id",
            "conversation_id",
            "role",
            "content",
            "images",
            "raw_response",
            "created_at",
        ]


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
