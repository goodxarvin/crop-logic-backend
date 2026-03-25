from rest_framework import serializers

from .models import Conversation, Message


class ConversationListSerializer(serializers.ModelSerializer):
    conversation_id = serializers.UUIDField(source="uuid", read_only=True)

    class Meta:
        model = Conversation
        fields = [
            "conversation_id",
            "title",
            "updated_at",
        ]


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
